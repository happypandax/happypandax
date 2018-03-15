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
import shelve
import rollbar
import importlib
import atexit
import ctypes
import subprocess
import logging

from dbm import dumb as dumbdb
from inspect import ismodule, currentframe, getframeinfo
from contextlib import contextmanager
from collections import namedtuple, UserList

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


def disable_loggers(logs):
    assert isinstance(logs, list)
    log_level = logging.WARNING
    for l in logs:
        if isinstance(l, str):
            hlogger.Logger(l).setLevel(log_level)
            lx = l + '.'
            if lx == constants.log_ns_core:
                hlogger.Logger("apscheduler").setLevel(log_level)
                hlogger.Logger("PIL").setLevel(log_level)
            elif lx == constants.log_ns_database:
                hlogger.Logger("sqlalchemy").setLevel(log_level)
                hlogger.Logger("sqlalchemy.pool").setLevel(log_level)
                hlogger.Logger("sqlalchemy.engine").setLevel(log_level)
                hlogger.Logger("sqlalchemy.orm").setLevel(log_level)
            elif lx == constants.log_ns_client:
                hlogger.Logger("geventwebsocket").setLevel(log_level)
            elif lx == constants.log_ns_network:
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

    parser.add_argument('-d', '--debug', action='store_true',
                        help='Start in debug mode (collects more information)')

    parser.add_argument('-i', '--interact', action='store_true',
                        help='Start in interactive mode')

    parser.add_argument('-v', '--version', action='version',
                        version='HappyPanda X {}#{}'.format(constants.version, constants.build))

    parser.add_argument('--safe', action='store_true',
                        help='Start without plugins')

    parser.add_argument('-x', '--dev', action='store_true',
                        help='Start in development mode')

    parser.add_argument('--only-web', action='store_true',
                        help='Start only the webserver (useful for debugging)')

    parser.add_argument('--momo', nargs=argparse.REMAINDER,
                        help='Reserved (Momo best girl)')

    return parser


def parse_options(args):
    "Parses args from the command-line"
    assert isinstance(args, argparse.Namespace)

    constants.dev = args.dev

    cfg = config.config

    cmd_args = {}

    if args.debug is not None:
        cmd_args.setdefault(config.debug.namespace, {})[config.debug.name] = args.debug

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

    if constants.dev:
        sys.displayhook == pprint.pprint

    if args.momo:
        run_with_privileges(*args.momo)


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
    importers = map(pkgutil.get_importer, pkg.__path__)
    toc = set()
    for i in importers:
        #log.d("importer:", i)
        if hasattr(i, 'toc'):
            #log.d("toc:", i.toc)
            toc |= i.toc
    for elm in toc:
        if elm.startswith(prefix):
            mods.append(elm)

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


def convert_to_json(buffer, name):
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
    return pprint.pformat(dict(
        ARCH=platform.machine(),
        VERSION=platform.version(),
        PLATFORM=platform.platform(),
        PYTHON=platform.python_version()
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
                         platform.platform()))
        hlogger.Logger.report_online = True


@contextmanager
def intertnal_db():
    log.d("Opening internal db")
    try:
        db = shelve.Shelf(dumbdb.open(constants.internal_db_path))
    except BaseException:
        log.e("Failed to open internal db")
        raise
    try:
        yield db
    finally:
        db.close()


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
        print("hi")
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


class AttributeList(UserList):
    """
    l = AttributeList("one", "two")
    l.one == "one"
    l.two == "two"

    """

    def __init__(self, *names):
        self._names = {str(x): x for x in names}
        super().__init__(names)

    def __getattr__(self, key):
        if key in self._names:
            return self._names[key]
        raise AttributeError("AttributeError: no attribute named '{}'".format(key))
