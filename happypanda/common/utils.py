import sys
import json
import enum
import os
import socket
import argparse
import pkgutil
import pprint
from inspect import ismodule

from happypanda.common import constants, exceptions, upnp

def eprint(*args, **kwargs):
    "Prints to stderr"
    print(*args, file=sys.stderr, **kwargs)


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
    pass

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
    return [(x, y) for x, y, _ in pkgutil.walk_packages(pkg.__path__)]

def get_module_members(mod):
    "Retrive list of members in modules"
    assert ismodule(mod)

## SERVER ##
def convert_to_json(buffer, name):
    ""
    try:
        if buffer.endswith(constants.postfix):
            buffer = buffer[:-len(constants.postfix)].decode('utf-8') # slice 'end' off
        json_data = json.loads(buffer)
    except json.JSONDecodeError as e:
        raise exceptions.JSONParseError(buffer, name, "Failed parsing json data: {}".format(e))
    return json_data

