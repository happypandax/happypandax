import sys
import json
import enum
import os
import socket

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

def setup_dirs():
    "Creates directories at the specified root path"
    pass

def connection_params(web=False):
    "Retrieve host and port"
    host = constants.host

    ## do a portfoward
    #if constants.public_server:
    #    try:
    #        upnp.ask_to_open_port(constants.local_port, "Happypanda X Server", protos=('TCP',))
    #        upnp.ask_to_open_port(constants.web_port, "Happypanda X Web Server", protos=('TCP',))
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