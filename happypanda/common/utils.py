import sys
import json
import enum
import os
import socket

from happypanda.common import constants, exceptions

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
    if web:
        params = (host, constants.web_port)
        return params
    else:
        if constants.public_server:
            # TODO: finish this
            # Note: upnpc
            raise NotImplementedError
        else:
            params = (host, constants.local_port)
        return params

## SERVER ##

def convert_to_json(buffer, name):
    ""
    try:
        json_data = json.loads(buffer[:-len(constants.postfix)].decode('utf-8')) # slice 'end' off
    except json.JSONDecodeError as e:
        raise exceptions.JSONParseError(buffer, name, "Failed parsing json data: {}".format(e))
    return json_data