import sys
import json
import os
import argparse
import pkgutil
import pprint
import base64
import uuid
import tempfile
import socket
import traceback
import gevent
import platform
import threading
import i18n
import rollbar
import importlib
import atexit
import ctypes
import subprocess
import logging
import regex
import OpenSSL
import errno
import collections
import langcodes

from inspect import ismodule, currentframe, getframeinfo
from contextlib import contextmanager
from collections import namedtuple
from gevent import ssl

from happypanda.common import constants, exceptions, hlogger, config
try:
    import winreg
except ImportError:  # only available on windows
    pass

log = hlogger.Logger(constants.log_ns_misc + __name__)

ImageSize = namedtuple("ImageSize", ['width', 'height'])

temp_dirs = []

i18n.load_path.append(constants.dir_translations)
i18n.set("file_format", "yaml")
i18n.set("filename_format", "{locale}.{namespace}.{format}")
i18n.set("error_on_missing_translation", True)


def setup_i18n():
    i18n.set("locale", config.translation_locale.value)
    i18n.set("fallback", "en_us")


def setup_dirs():
    "Creates directories at the specified root path"
    for dir_x in (
            constants.dir_data,
            constants.dir_certs,
            constants.dir_cache,
            constants.dir_log,
            constants.dir_plugin,
            constants.dir_temp,
            constants.dir_static,
            constants.dir_thumbs,
            constants.dir_templates,
            constants.dir_translations
    ):
        if dir_x:
            if not os.path.isdir(dir_x):
                os.makedirs(dir_x)


def enable_loggers(logs):
    assert isinstance(logs, list)
    log_level = logging.WARNING
    if logs:
        for l in constants.log_namespaces:
            if l not in logs:
                hlogger.Logger(l).setLevel(log_level)
                if l in constants.log_ns_core:
                    hlogger.Logger("apscheduler").setLevel(log_level)
                    hlogger.Logger("PIL").setLevel(log_level)
                elif l in constants.log_ns_database:
                    hlogger.Logger("sqlalchemy").setLevel(log_level)
                    hlogger.Logger("sqlalchemy.pool").setLevel(log_level)
                    hlogger.Logger("sqlalchemy.engine").setLevel(log_level)
                    hlogger.Logger("sqlalchemy.orm").setLevel(log_level)
                    hlogger.Logger("alembic").setLevel(log_level)
                elif l in constants.log_ns_client:
                    hlogger.Logger("geventwebsocket").setLevel(log_level)
                elif l in constants.log_ns_network:
                    hlogger.Logger("cachecontrol").setLevel(log_level)


def get_argparser():
    "Creates and returns a command-line arguments parser"
    parser = argparse.ArgumentParser(
        prog="HappyPanda X",
        description="A manga/doujinshi manager with tagging support (https://github.com/happypandax/server)")

    parser.add_argument('-p', '--port', type=int,
                        help='Specify which port to start the server on (default: {})'.format(config.port.default))

    parser.add_argument(
        '--torrent-port',
        type=int,
        help='Specify which port to start the torrent client on (default: {})'.format(config.port_torrent.default))

    parser.add_argument(
        '--web-port',
        type=int,
        help='Specify which port to start the webserver on (default: {})'.format(config.port_web.default))

    parser.add_argument('--host', type=str,
                        help='Specify which address the server should bind to (default: {})'.format(config.host.default))

    parser.add_argument('--web-host', type=str,
                        help='Specify which address the webserver should bind to (defualt: {})'.format(config.host_web.default))

    parser.add_argument('--gen-config', action='store_true',
                        help='Generate a skeleton example config file and quit')

    parser.add_argument('--create-user', action='store_true',
                        help='Create a user interactively and quit')

    parser.add_argument('--delete-user', type=str, metavar="USERNAME",
                        help='Delete a user interactively and quit')

    parser.add_argument('--list-users', type=int, metavar="PAGE",
                        nargs="?", const=1,
                        help='Display a list of users from page N and quit')

    parser.add_argument('-d', '--debug', action='store_true',
                        help='Start in debug mode (collects more information)')

    parser.add_argument('-i', '--interact', action='store_true',
                        help='Start in interactive mode')

    parser.add_argument('-v', '--version', action='version',
                        version='HappyPanda X {}#{}'.format(constants.version, constants.build))

    parser.add_argument('--safe', action='store_true',
                        help='Start without plugins')

    parser.add_argument('-x', '--dev', action='store_true',
                        help='Start in development mode (redirects logging to stdout)')

    parser.add_argument('--dev-db', action='store_true',
                        help='Create and use a development database')

    parser.add_argument('--only-web', action='store_true',
                        help='Start only the webserver (useful for debugging)')

    parser.add_argument('--momo', nargs=argparse.REMAINDER,
                        help='Reserved for best girl Momo')

    return parser


def parse_options(args):
    "Parses args from the command-line"
    assert isinstance(args, argparse.Namespace)

    constants.dev = args.dev

    cfg = config.config

    cmd_args = {}
    if args.debug:
        cmd_args.setdefault(config.debug.namespace, {})[config.debug.name] = args.debug

    if args.dev_db:
        cmd_args.setdefault(config.dev_db.namespace, {})[config.dev_db.name] = args.dev_db

    if args.host is not None:
        cmd_args.setdefault(config.host.namespace, {})[config.host.name] = args.host

    if args.port is not None:
        cmd_args.setdefault(config.port.namespace, {})[config.port.name] = args.port

    if args.web_host is not None:
        cmd_args.setdefault(config.host_web.namespace, {})[config.host_web.name] = args.web_host

    if args.web_port is not None:
        cmd_args.setdefault(config.port_web.namespace, {})[config.port_web.name] = args.web_port

    if args.torrent_port is not None:
        cmd_args.setdefault(config.port_torrent.namespace, {})[config.port_torrent.name] = args.torrent_port

    if cmd_args:
        cfg.apply_commandline_args(cmd_args)

    constants.dev_db = config.dev_db.value

    if constants.dev:
        sys.displayhook == pprint.pprint

    if args.momo:
        run_with_privileges(*args.momo)


def get_input(txt="Please enter something...", func=None):
    if not func:
        def func():
            return get_input("input: ")
    t = func()
    while not t:
        print(txt)
        t = func()
    return t


def connection_params():
    "Retrieve host and port"
    params = (config.host.value if config.host.value else "localhost", config.port.value)
    return params


def get_package_modules(pkg, load=True):
    "Retrieve list of modules in package"
    assert ismodule(pkg) and hasattr(pkg, '__path__')
    mods = []
    prefix = pkg.__name__ + "."
    mods = [m[1] for m in pkgutil.iter_modules(pkg.__path__, prefix)]

    # special handling for PyInstaller
    if hasattr(pkg, '__loader__') and hasattr(pkg.__loader__, 'toc'):
        [mods.append(x) for x in pkg.__loader__.toc if x.startswith(prefix)]

    return [importlib.import_module(x) for x in mods] if load else mods


def get_module_members(mod):
    "Retrieve list of members in modules"
    assert ismodule(mod)
    raise NotImplementedError


def imagetobase64(data):
    "Convert image from bytes to base64 string"
    return base64.encodestring(data).decode(encoding='utf-8')


def imagefrombase64(data):
    "Convert base64 string to bytes"
    return base64.decodestring(data)


def all_subclasses(cls):
    "Return all subclasses of given class"
    return cls.__subclasses__() + [g for s in cls.__subclasses__()
                                   for g in all_subclasses(s)]


@contextmanager
def session(sess=constants.db_session):
    s = sess()
    try:
        yield s
        s.commit()
    except BaseException:
        s.rollback()
        raise


def convert_to_json(buffer, name, log=log):
    ""
    try:
        log.d("Converting", sys.getsizeof(buffer), "bytes to JSON")
        if buffer.endswith(constants.postfix):
            buffer = buffer[:-len(constants.postfix)]  # slice eof mark off
        if isinstance(buffer, bytes):
            buffer = buffer.decode('utf-8')
        json_data = json.loads(buffer)
    except json.JSONDecodeError as e:
        raise exceptions.JSONParseError(
            buffer, name, "Failed parsing JSON data: {}".format(e))
    if constants.dev:
        log.d("data:\n", json_data)
    return json_data


def end_of_message(bytes_):
    "Checks if EOF has been reached. Returns splitted data and bool."
    assert isinstance(bytes_, bytes)

    if constants.postfix in bytes_:
        return tuple(bytes_.split(constants.postfix, maxsplit=1)), True
    return bytes_, False


def generate_key(length=10):
    "Generate a random URL-safe key"
    return base64.urlsafe_b64encode(
        os.urandom(length)).rstrip(b'=').decode('ascii')


def random_name():
    "Generate a random urlsafe name and return it"
    r = base64.urlsafe_b64encode(uuid.uuid4().bytes).decode('utf-8').replace('=', '').replace('_', '-')
    return r


def this_function():
    "Return name of current function"
    return getframeinfo(currentframe()).function


def this_command(command_cls):
    "Return name of command for exceptions"
    return "Command:" + command_cls.__class__.__name__


def create_temp_dir():
    t = tempfile.TemporaryDirectory(dir=constants.dir_temp)
    temp_dirs.append(t)
    return t


def get_qualified_name(host, port):
    "Returns host:port"
    assert isinstance(host, str)
    if not host:
        host = 'localhost'
    elif host == '0.0.0.0':
        host = get_local_ip()
    # TODO: public ip
    return host.strip() + ':' + str(port).strip()


def get_local_ip():
    if not constants.local_ip:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            # doesn't even have to be reachable
            s.connect(('10.255.255.255', 1))
            IP = s.getsockname()[0]
        except BaseException:
            IP = '127.0.0.1'
        finally:
            s.close()
        constants.local_ip = IP
    return constants.local_ip


def exception_traceback(self, ex):
    return [line.rstrip('\n') for line in
            traceback.format_exception(ex.__class__, ex, ex.__traceback__)]


def switch(priority=constants.Priority.Normal):
    assert isinstance(priority, constants.Priority)
    if not in_cpubound_thread() and constants.server_started:
        gevent.idle(priority.value)


def in_cpubound_thread():
    return getattr(threading.local(), 'in_cpubound_thread', False)


def get_context(key="ctx"):
    "Get a dict local to the spawn tree of current greenlet"
    l = getattr(gevent.getcurrent(), 'locals', None)
    if key is not None and l:
        return l[key]
    return l


def os_info():
    return pprint.pformat((
        platform.machine(),
        platform.platform(),
    ))


def setup_online_reporter():
    """
    WARNING:
        execute AFTER setting up a logger!
        the rollbar lib somehow messes it up!
    """
    if config.report_critical_errors.value and constants.is_frozen:

        rollbar.init(config.rollbar_access_token.value,
                     'HPX {} web({}) db({}) build({}) platform({})'.format(
                         constants.version,
                         constants.version_web,
                         constants.version_db,
                         constants.build,
                         "windows" if constants.is_win else "linux" if constants.is_linux else "osx" if constants.is_osx else "unknown"),
                     allow_logging_basic_config=False,
                     suppress_reinit_warning=True)
        hlogger.Logger.report_online = True


def restart_process():
    """
    Restart process. This function will never return.
    """
    if constants.is_frozen:
        os.execv(sys.executable, ["python"] + sys.argv[1:])  # looks like this [path, *real_args]
    else:
        os.execv(sys.executable, ["python"] + sys.argv)


def launch_updater():
    upd_name = constants.updater_name
    if constants.is_win:
        upd_name += '.exe'
    atexit.register(os.execl, upd_name, upd_name)


@contextmanager
def temp_cwd(p):
    "Temp change the current working directory"
    o = os.getcwd()
    os.chdir(p)
    yield
    os.chdir(o)


def error_check_socket(host=None, port=None):
    if port is not None:
        try:
            int(port)
        except ValueError:
            raise


def win32_set_reg(path, name, value):
    if not constants.is_win:
        raise OSError("Only supported on Windows")
    try:
        winreg.CreateKey(winreg.HKEY_CURRENT_USER, path)
        registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0,
                                      winreg.KEY_WRITE)
        winreg.SetValueEx(registry_key, name, 0, winreg.REG_SZ, value)
        winreg.CloseKey(registry_key)
        return True
    except OSError:
        return False


def win32_get_reg(path, name):
    if not constants.is_win:
        raise OSError("Only supported on Windows")
    try:
        registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0,
                                      winreg.KEY_READ)
        value, regtype = winreg.QueryValueEx(registry_key, name)
        winreg.CloseKey(registry_key)
        return value
    except OSError:
        return None


def win32_del_reg(path, name):
    if not constants.is_win:
        raise OSError("Only supported on Windows")
    try:
        registry_key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, path, 0,
                                      winreg.KEY_WRITE)
        winreg.DeleteValue(registry_key, name)
        winreg.CloseKey(registry_key)
        return True
    except OSError as e:
        return False


def add_to_startup(name, executable):
    if constants.is_win:
        return win32_set_reg(r"Software\Microsoft\Windows\CurrentVersion\Run",
                             name, '"{}"'.format(executable))


def remove_from_startup(name):
    if constants.is_win:
        return win32_del_reg(r"Software\Microsoft\Windows\CurrentVersion\Run",
                             name)


def is_elevated():
    if constants.is_win:
        try:
            return ctypes.windll.shell32.isUserAnAdmin()
        except BaseException:
            return False


def run_with_privileges(func, *args):
    if is_elevated():
        import time
        time.sleep(10)
    else:
        prog = constants.executable_name if constants.is_frozen else sys.executable
        params = []
        if not constants.is_frozen:
            params = ['run.py']
        params += ['--momo'] + list(args)

        if constants.is_win:
            print(prog)
            ctypes.windll.shell32.ShellExecuteW(None, "runas", prog, subprocess.list2cmdline(params), None, 1)


def multi_word_extract(cand, word_list, case=False, sep=" ", startswith=False, allow_inbetween=True):
    """
    Extract candidate words in the list of words and returns them.
    Like extract_original_text but with prepared words.

    func("foo bar", ["Foo", "Bar"]) -> "Foo Bar"
    """

    if isinstance(word_list, str):
        word_list = word_list.split(sep)

    if not allow_inbetween:
        word_list = [word_list]

    for n, word in enumerate(word_list):
        wlist = word_list.copy()[n:] if allow_inbetween else word
        buffer = ""
        swith_cand = ""
        while wlist:
            t = wlist.pop(0)
            if buffer:
                buffer += sep + t
            else:
                buffer = t

            a = buffer if case else buffer.lower()
            b = cand if case else cand.lower()

            if startswith:
                m = b.startswith(a)
            else:
                m = b == a
            if m and startswith:
                swith_cand = buffer
            elif m:
                return buffer
            else:
                if swith_cand:
                    return swith_cand
        else:
            if swith_cand:
                return swith_cand


def extract_original_text(cand, text):
    """
    Extract candidate text from a long string of text with correct case.

    func("foo bar", "momo [Foo Bar] yumiko") -> "Foo Bar"
    """
    r = r"((?<=[\( \[]))?({})((?=[\) \]$]))?".format(cand)
    m = regex.search(r, text, regex.IGNORECASE | regex.UNICODE)
    if m:
        return m[0]
    return cand


def capitalize_text(text):
    """
    better str.capitalize
    """
    return " ".join(x.capitalize() for x in text.strip().split())


def indent_text(txt, num=4):
    """
    """
    if isinstance(txt, str):
        txt = txt.split('\n')
    return "\n".join((num * " ") + i for i in txt)


def remove_multiple_spaces(txt):
    """
    Also removes whitespace characters (tab, newline, etc.)
    """
    return " ".join(txt.split())


def regex_first_group(rgx):
    """
    """
    r = []
    for x in rgx:
        if isinstance(x, tuple):
            x = x[0]
        r.append(x)
    return tuple(r)


def get_language_code(lcode):
    assert isinstance(lcode, str)
    if '_' in lcode:
        lcode = lcode.split('_')[0]
    return lcode.lower()


def create_ssl_context(webserver=False, server_side=False, verify_mode=ssl.CERT_OPTIONAL, check_hostname=False,
                       certfile=None, keyfile=None):

    c = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH if server_side else ssl.Purpose.SERVER_AUTH)

    if verify_mode is not None:
        c.verify_mode = verify_mode
    if check_hostname is not None:
        c.check_hostname = check_hostname

    if not certfile:
        cfg_cert = config.web_cert.value if webserver else config.server_cert.value
        certfile = cfg_cert.get("certfile")
        keyfile = cfg_cert.get("keyfile")
        if certfile is None and webserver:
            cfg_cert = config.server_cert.value
            certfile = cfg_cert.get("certfile")
            keyfile = cfg_cert.get("keyfile")

    if certfile is None:
        certfile = os.path.join(constants.dir_certs, "happypandax.crt")
        keyfile = os.path.join(constants.dir_certs, "happypandax.key")
        pemfile = os.path.join(constants.dir_certs, "happypandax.pem")
        pfxfile = os.path.join(constants.dir_certs, "happypandax.pfx")
        if not os.path.exists(certfile):
            create_self_signed_cert(certfile, keyfile, pemfile, pfxfile)
        if not os.path.exists(pfxfile):
            export_cert_to_pfx(pfxfile, certfile, keyfile)
        if server_side and not webserver:
            log.i("Certs not provided, using self-signed certificate", stdout=True)
    else:
        if not os.path.exists(certfile) and not (os.path.exists(keyfile) if keyfile else False):
            raise exceptions.CoreError(this_function(), "Non-existent certificate or private key file")

    if not keyfile:
        keyfile = None

    try:
        if server_side:
            c.load_cert_chain(certfile=certfile, keyfile=keyfile)
        else:
            c.load_verify_locations(certfile)
    except OSError as e:
        if e.errno == errno.EINVAL:
            raise exceptions.CoreError(this_function(), "Invalid certificate or private key filepath")
        raise exceptions.CoreError(this_function(), "Invalid certificate or private key: {}".format(e))

    return c


def create_self_signed_cert(cert_file, key_file, pem_file=None, pfx_file=None):
    """
    self-signed cert
    """

    # create a key pair
    k = OpenSSL.crypto.PKey()
    k.generate_key(OpenSSL.crypto.TYPE_RSA, 2048)

    # create a self-signed cert
    cert = OpenSSL.crypto.X509()
    cert.set_version(2)
    cert.get_subject().C = "HP"
    cert.get_subject().ST = "HappyPanda X"
    cert.get_subject().L = "HappyPanda X"
    cert.get_subject().O = "HappyPanda X"
    cert.get_subject().OU = "Twiddly Inc"
    cert.get_subject().CN = "localhost"
    cert.set_serial_number(1000)
    cert.gmtime_adj_notBefore(0)
    cert.gmtime_adj_notAfter(10 * 365 * 24 * 60 * 60)
    cert.set_issuer(cert.get_subject())
    cert.set_pubkey(k)

    san_list = ["DNS:localhost",
                "DNS:happypanda.local",
                "DNS:happypandax.local",
                "IP:127.0.0.1",
                "IP:::1",  # IPv6
                ]
    l_ip = get_local_ip()
    if l_ip != "127.0.0.1":
        san_list.append("IP:{}".format(l_ip))

    cert.add_extensions([
        OpenSSL.crypto.X509Extension(b"basicConstraints", False, "CA:TRUE, pathlen:0".encode()),
        OpenSSL.crypto.X509Extension(b"subjectAltName", False, ", ".join(san_list).encode()),
    ])

    cert.sign(k, 'sha256')

    with open(cert_file, "wb") as f:
        cert_pem = OpenSSL.crypto.dump_certificate(OpenSSL.crypto.FILETYPE_PEM, cert)
        f.write(cert_pem)
    with open(key_file, "wb") as f:
        key_pem = OpenSSL.crypto.dump_privatekey(OpenSSL.crypto.FILETYPE_PEM, k)
        f.write(key_pem)

    if pem_file:
        with open(pem_file, "wb") as f:
            f.write(cert_pem + key_pem)

    if pfx_file:
        export_cert_to_pfx(pfx_file, cert_file, key_file)


def export_cert_to_pfx(pfx_file, cert_file, key_file):
    with open(cert_file, "rb") as f:
        c = OpenSSL.crypto.load_certificate(OpenSSL.crypto.FILETYPE_PEM, f.read())
    with open(key_file, "rb") as f:
        k = OpenSSL.crypto.load_privatekey(OpenSSL.crypto.FILETYPE_PEM, f.read())
    pfx = OpenSSL.crypto.PKCS12Type()
    pfx.set_certificate(c)
    pfx.set_privatekey(k)
    with open(pfx_file, "wb") as f:
        f.write(pfx.export())  # pfx.export("password")


def log_exception(f=None, log=log):
    if f is None:
        def p_wrap(f):
            return log_exception(f, log)
        return p_wrap
    else:
        def wrapper(*args, **kwargs):
            try:
                v = f(*args, **kwargs)
            except BaseException:
                log.exception()
                raise
            return v
        return wrapper


def json_dumps(msg, log=log):
    try:
        return json.dumps(msg)
    except BaseException:
        log.e(msg)
        raise


def check_signature():
    pass
    #sig = inspect.signature(node.plugin.__init__)
    #pars = list(sig.parameters)
    # if not len(pars) == 3:
    #    raise exceptions.PluginSignatureError(
    #        node, "Unexpected __init__() signature")
    #var_pos = False
    #var_key = False
    # for a in pars:
    #    if sig.parameters[a].kind == inspect.Parameter.VAR_POSITIONAL:
    #        var_pos = True
    #    elif sig.parameters[a].kind == inspect.Parameter.VAR_KEYWORD:
    #        var_key = True


def language_to_code(language_name):
    """
    """
    code = ""
    try:
        l = langcodes.find(language_name)
        code = l.language
    except LookupError:
        pass
    return code


def get_real_file(path):
    """
    """
    if path.endswith(constants.link_ext):
        with open(path, 'r', encoding='utf-8') as fp:
            path = fp.read()
    return path


def is_collection(obj):
    if isinstance(obj, str):
        return False
    return hasattr(type(obj), '__iter__')


def is_url(url, strict=False):
    t = ("https://", "http://")
    if not strict:
        t += ("www.",)
    return url.lower().startswith(t)


def dict_merge(dct, merge_dct):
    """ Recursive dict merge. Inspired by :meth:``dict.update()``, instead of
    updating only top-level keys, dict_merge recurses down into dicts nested
    to an arbitrary depth, updating keys. The ``merge_dct`` is merged into
    ``dct``.
    :param dct: dict onto which the merge is executed
    :param merge_dct: dct merged into dct
    """
    for k in merge_dct:
        if (k in dct and isinstance(dct[k], dict)
                and isinstance(merge_dct[k], collections.Mapping)):
            dict_merge(dct[k], merge_dct[k])
        else:
            dct[k] = merge_dct[k]
    return dct


def compare_json_dicts(a, b):
    """
    Compare two JSON compatible dicts
    """
    a_j = json.dumps(a, sort_keys=True, indent=2)
    b_j = json.dumps(a, sort_keys=True, indent=2)
    return a_j == b_j
