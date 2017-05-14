import sys
import json
import enum
import os
import socket
import argparse
import pkgutil
import pprint
import logging
from inspect import ismodule
from logging.handlers import RotatingFileHandler

from happypanda.common import constants, exceptions, upnp

## LOGGER ##

def eprint(*args, **kwargs):
    "Prints to stderr"
    print(*args, file=sys.stderr, **kwargs)

class Logger:

    def __init__(self, name):
        self._logger = logging.getLogger(name)

    def exception(self, *args):
        ""
        self._log(self._logger.exception, *args)

    def i(self, *args):
        "INFO"
        self._log(self._logger.info, *args)

    def d(self, *args):
        "INFO"
        self._log(self._logger.debug, *args)

    def w(self, *args):
        "INFO"
        self._log(self._logger.warning, *args)

    def e(self, *args):
        "INFO"
        self._log(self._logger.error, *args)

    def c(self, *args):
        "INFO"
        self._log(self._logger.critical, **args)

    def _log(self, level, *args):
        s = ""
        for a in args:
            if not isinstance(a, str):
                a = pprint.pformat(a)
            s += a
            s += " "
        level(s)

log = Logger(__name__)

## PATH ##
class PathType(enum.Enum):
    Directoy = 1
    Archive = 2
    Invalid = 3

    @staticmethod
    def check(path):
        if os.path.isdir(path):
            return PathType.Directoy
        head, ext = os.path.splitext(path.lower())
        if ext in constants.supported_archives:
            return PathType.Archive

        return PathType.Invalid

## Core ##
def setup_dirs():
    "Creates directories at the specified root path"
    for dir_x in (constants.dir_cache, constants.dir_data, constants.dir_log, constants.dir_plugin):
        if dir_x:
            if not os.path.isdir(dir_x):
                os.mkdir(dir_x)

def setup_logger(args):
    assert isinstance(args, argparse.Namespace)
    log_handlers = []
    log_level = logging.INFO
    if args.dev:
        log_handlers.append(logging.StreamHandler())
    else:
        logging.raiseExceptions = False # Don't raise exception if in production mode

    if args.debug:
        print("{} created at {}".format(constants.log_debug, os.path.join(os.getcwd(),constants.dir_log)))
        try:
            with open(constants.log_debug, 'x') as f:
                pass
        except FileExistsError:
            pass

        lg = logging.FileHandler(constants.log_debug, 'w', 'utf-8')
        lg.setLevel(logging.DEBUG)
        log_handlers.append(lg)
        log_level = logging.DEBUG

    for log_path, lvl in ((constants.log_normal, logging.INFO), (constants.log_error, logging.ERROR)):
        try:
            with open(log_path, 'x') as f:
                pass
        except FileExistsError: pass
        lg = RotatingFileHandler(log_path, maxBytes=100000 * 10, encoding='utf-8', backupCount=1)
        lg.setLevel(lvl)
        log_handlers.append(lg)

    logging.basicConfig(level=log_level,
                    format='%(asctime)-8s %(levelname)-10s %(name)-10s %(message)s',
                    datefmt='%d-%m %H:%M',
                    handlers=tuple(log_handlers))

def get_argparser():
    "Creates and returns a command-line arguments parser"
    parser = argparse.ArgumentParser(prog="Happypanda X",
        description="A manga/doujinshi manager with tagging support")

    parser.add_argument('-w', '--web', action='store_true',
                    help='Start the webserver')

    parser.add_argument('-p', '--port', type=int,
                    help='Specify which port to start the server on')

    parser.add_argument('--web-port', type=int,
                    help='Specify which port to start the web server on')

    parser.add_argument('--localhost', action='store_true',
                    help='Start servers on localhost')

    parser.add_argument('-d', '--debug', action='store_true',
                    help='Start in debug mode')

    parser.add_argument('-i', '--interact', action='store_true',
                    help='Start in interactive mode')

    parser.add_argument('-v', '--version', action='version',
                    version='Happypanda X v{}'.format(constants.version))

    parser.add_argument('--safe', action='store_true',
                    help='Start without plugins')

    parser.add_argument('-x', '--dev', action='store_true',
                    help='start in development mode')

    return parser

def parse_options(args):
    "Parses args from the command-line"
    assert isinstance(args, argparse.Namespace)

    constants.debug = args.debug
    if constants.debug:
        sys.displayhook == pprint.pprint
    constants.localhost = args.localhost
    if args.port:
        constants.local_port = args.port
    if args.web_port:
        constants.web_port = args.web_port

def connection_params(web=False):
    "Retrieve host and port"
    host = constants.host

    ## do a portfoward
    #if constants.public_server:
    #    try:
    #        upnp.ask_to_open_port(constants.local_port, "Happypanda X Server",
    #        protos=('TCP',))
    #        upnp.ask_to_open_port(constants.web_port, "Happypanda X Web
    #        Server", protos=('TCP',))
    #    except upnp.UpnpError as e:
    #        constants.public_server = False
    #        # log
    #        # inform user

    if web:
        params = (host, constants.web_port)
        return params
    else:
        params = (host, constants.local_port)
        return params

def get_package_modules(pkg):
    "Retrive list of modules in package"
    assert ismodule(pkg) and hasattr(pkg, '__path__')
    mods = []
    for importer, modname, ispkg in pkgutil.iter_modules(pkg.__path__, pkg.__name__+"."):
        mods.append(importer.find_module(modname).load_module(modname))
    return mods

def get_module_members(mod):
    "Retrive list of members in modules"
    assert ismodule(mod)
    raise NotImplementedError

## SERVER ##
def convert_to_json(buffer, name):
    ""
    try:
        log.d("Converting", sys.getsizeof(buffer),"bytes to JSON")
        if buffer.endswith(constants.postfix):
            buffer = buffer[:-len(constants.postfix)] # slice eof mark off
        if isinstance(buffer, bytes):
            buffer = buffer.decode('utf-8')
        json_data = json.loads(buffer)
    except json.JSONDecodeError as e:
        raise exceptions.JSONParseError(buffer, name, "Failed parsing json data: {}".format(e))
    return json_data


def end_of_message(bytes_):
    "Checks if EOF has been reached. Returns bool splitted data."
    assert isinstance(bytes_, bytes)

    if constants.postfix in bytes_:
        return tuple(bytes_.split(constants.postfix, maxsplit=1)), True
    return bytes_, False


class APIEnum(enum.Enum):
    "A conv. enum class allowing for str comparison"

    @classmethod
    def get(cls, key, default=None):
        try:
            v = cls[key]
        except KeyError:
            v = default
        return v