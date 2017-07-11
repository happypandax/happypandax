import sys
import json
import enum
import os
import argparse
import pkgutil
import pprint
import logging
import base64
import uuid
import tempfile

from inspect import ismodule, currentframe, getframeinfo
from logging.handlers import RotatingFileHandler
from contextlib import contextmanager
from collections import namedtuple

from happypanda.common import constants, exceptions, hlogger

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
            constants.dir_thumbs):
        if dir_x:
            if not os.path.isdir(dir_x):
                os.makedirs(dir_x)

def setup_logger(args):
    assert isinstance(args, argparse.Namespace)
    log_handlers = []
    log_level = logging.INFO
    if args.dev:
        log_handlers.append(logging.StreamHandler())
    else:
        logging.raiseExceptions = False  # Don't raise exception if in production mode

    if args.debug:
        print(
            "{} created at {}".format(
                constants.log_debug,
                os.path.join(
                    os.getcwd(),
                    constants.dir_log)))
        try:
            with open(constants.log_debug, 'x') as f:
                pass
        except FileExistsError:
            pass

        lg = logging.FileHandler(constants.log_debug, 'w', 'utf-8')
        lg.setLevel(logging.DEBUG)
        log_handlers.append(lg)
        log_level = logging.DEBUG

    for log_path, lvl in ((constants.log_normal, logging.INFO),
                          (constants.log_error, logging.ERROR)):
        try:
            with open(log_path, 'x') as f:  # noqa: F841
                pass
        except FileExistsError:
            pass
        lg = RotatingFileHandler(
            log_path,
            maxBytes=100000 * 10,
            encoding='utf-8',
            backupCount=1)
        lg.setLevel(lvl)
        log_handlers.append(lg)

    logging.basicConfig(
        level=log_level,
        format='%(asctime)-8s %(levelname)-10s %(name)-10s %(message)s',
        datefmt='%d-%m %H:%M',
        handlers=tuple(log_handlers))


def get_argparser():
    "Creates and returns a command-line arguments parser"
    parser = argparse.ArgumentParser(
        prog="Happypanda X",
        description="A manga/doujinshi manager with tagging support (https://github.com/happypandax/server)")

    parser.add_argument('-p', '--port', type=int, default=constants.port,
                        help='Specify which port to start the server on')

    parser.add_argument(
        '--torrent-port',
        type=int,
        default=constants.port_torrent,
        help='Specify which port to start the torrent client on')

    parser.add_argument('--host', type=str, default=constants.host,
                        help='Specify which address the server should bind to')

    parser.add_argument(
        '--expose',
        action='store_true',
        help='Attempt to expose the server through portforwading')

    parser.add_argument('--generate-config', action='store_true',
                        help='Generate a skeleton config file')

    parser.add_argument('-d', '--debug', action='store_true',
                        help='Start in debug mode (collects more information)')

    parser.add_argument('-i', '--interact', action='store_true',
                        help='Start in interactive mode')

    parser.add_argument('-v', '--version', action='version',
                        version='Happypanda X {}'.format(constants.version))

    parser.add_argument('--safe', action='store_true',
                        help='Start without plugins')

    parser.add_argument('-x', '--dev', action='store_true',
                        help='Start in development mode')

    return parser


def parse_options(args):
    "Parses args from the command-line"
    assert isinstance(args, argparse.Namespace)

    cfg = constants.config

    with cfg.namespace(constants.core_ns):

        constants.debug = cfg.update("debug", args.debug)
        constants.dev = args.dev
        constants.host = cfg.update("host", args.host)
        constants.expose_server = cfg.update("expose_server", args.expose)

        constants.port = cfg.update("port", args.port)
        constants.port_torrent = cfg.update("torrent_port", args.torrent_port)

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
    params = (constants.host, constants.port)
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
    "Convert base64 string to image"
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

class APIEnum(enum.Enum):
    "A conv. enum class allowing for str comparison"

    @classmethod
    def get(cls, key):
        try:
            v = cls[key]
            return v
        except KeyError:
            raise exceptions.ServerError(
                this_function(),
                "{}: enum doesn't exist '{}' (make sure capitalization is alright)".format(
                    cls.__name__,
                    key))


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
    return base64.urlsafe_b64encode(uuid.uuid4().bytes).decode('utf-8').replace('=','')

def require_context(ctx):
    assert ctx, "This function requires a context object"


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
