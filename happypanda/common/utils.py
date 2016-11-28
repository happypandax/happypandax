import sys
import socket
import time
import random
import json

from happypanda.common import constants, exceptions

def eprint(*args, **kwargs):
    "Prints to stderr"
    print(*args, file=sys.stderr, **kwargs)

def connectionParams(web=False):
    "Retrieve host and port"
    if web:
        params = (constants.host, constants.web_port)
        return params
    else:
        if constants.public_server:
            # TODO: finish this
            # Note: upnpc
            raise NotImplementedError
        else:
            params = (constants.host, constants.local_port)
        return params

## SERVER ##
class Client:
    """A common wrapper for communicating with server.

    Params:
        name -- name of client
    """

    def __init__(self, name):
        self.name = name
        self._server = (constants.host, constants.local_port)
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._alive = False
        self._versions = {}

    def alive(self):
        "Check if connection with the server is still alive"
        return self._alive

    def _connect(self):
        "Connect to the server"
        if not self._alive:
            try:
                self._sock.connect(self._server)
                self._alive = True
                # receive versions
                data = self._recv()
                print('data:', data)
                for x, y in tuple(zip(('server', 'database'), data['version'])):
                    self._versions[x] = y
            except socket.error:
                raise exceptions.ClientError(self.name, "Failed to establish server connection")

    def _recv(self):
        ""
        # log receive
        try:
            buffer = b''
            while not buffer.endswith(constants.postfix): # loose
                data = self._sock.recv(constants.data_size)
                if not data:
                    self._alive = False
                    raise exceptions.ServerDisconnectError(self.name, "Server disconnected")
                buffer += data
            # log received
            try:
                json_data = json.loads(buffer[:-len(constants.postfix)].decode('utf-8')) # slice 'end' off
            except json.JSONDecodeError as e:
                raise exceptions.JSONParseError(buffer, self.name, "Failed parsing json data: {}".format(e))
            return json_data
        except socket.error as e:
            # log disconnect
            self.alive = False
            raise exceptions.ServerError(self.name, "{}".format(e))

    def communicate(self, jsonmsg):
        """Send and receive data with server

        params:
            jsonmsg -- dict
        returns:
            json
        """
        # log send
        if self._alive:
            if isinstance(jsonmsg, dict):
                self._sock.sendall(jsonmsg)
                self._sock.sendall(constants.postfix)
            else:
                raise exceptions.ClientError(self.name, "jsonmsg must be a dict object")
            return self._recv()
        else:
            raise exceptions.ServerDisconnectError(self.name, "Server already disconnected")

    def close(self):
        "Close connection with server"
        self._alive = False
        self._sock.close()

