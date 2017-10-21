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

from inspect import ismodule, currentframe, getframeinfo
from contextlib import contextmanager
from collections import namedtuple, UserList

from happypanda.common import constants, exceptions, hlogger, config

log = hlogger.Logger(__name__)

ImageSize = namedtuple("ImageSize", ['width', 'height'])

temp_dirs = []


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


def get_argparser():
    "Creates and returns a command-line arguments parser"
    parser = argparse.ArgumentParser(
        prog="Happypanda X",
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

    # attempt to do a portfoward

    # if constants.public_server:
    #    try:
    #        upnp.ask_to_open_port(constants.local_port, "Happypanda X Server",
    #        protos=('TCP',))
    #        upnp.ask_to_open_port(constants.web_port, "Happypanda X Web
    #        Server", protos=('TCP',))
    #    except upnp.UpnpError as e:
    #        constants.public_server = False
    #        # log
    #        # inform user


def connection_params():
    "Retrieve host and port"
    params = (config.host.value, config.port.value)
    return params


def get_package_modules(pkg):
    "Retrive list of modules in package"
    assert ismodule(pkg) and hasattr(pkg, '__path__')
    mods = []
    for importer, modname, ispkg in pkgutil.iter_modules(
            pkg.__path__, pkg.__name__ + "."):
        mods.append(importer.find_module(modname).load_module(modname))
    return mods


def get_module_members(mod):
    "Retrive list of members in modules"
    assert ismodule(mod)
    raise NotImplementedError


def imagetobase64(data):
    "Convert image from bytes to base64 string"
    return base64.encodestring(data).decode(encoding='utf-8')


def imagefrombase64(data):
    "Convert base64 string to bytes"
    return base64.decodestring(data)


def all_subclasses(cls):
    return cls.__subclasses__() + [g for s in cls.__subclasses__()
                                   for g in all_subclasses(s)]


@contextmanager
def session(sess=constants.db_session):
    s = sess()
    try:
        yield s
        s.commit()
    except:
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
            buffer, name, "Failed parsing json data: {}".format(e))
    if constants.dev:
        log.d("data:\n", json_data)
    return json_data


def end_of_message(bytes_):
    "Checks if EOF has been reached. Returns bool splitted data."
    assert isinstance(bytes_, bytes)

    if constants.postfix in bytes_:
        return tuple(bytes_.split(constants.postfix, maxsplit=1)), True
    return bytes_, False


def generate_key(length=10):
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
    if not host or host == '0.0.0.0':
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
        except:
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
    gevent.idle(priority.value)


def get_context(key="ctx"):
    "Get a dict local to the spawn tree of current greenlet"
    l = getattr(gevent.getcurrent(), 'locals', None)
    if key is not None:
        return l[key]
    return l


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
