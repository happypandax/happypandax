import socket
import sys
import json

from happypanda.common import constants, exceptions, utils, message

log = utils.Logger(__name__)


class Client:
    """A common wrapper for communicating with server.

    Params:
        name -- name of client
    """

    def __init__(self, name, client_id=None):
        self.name = name
        self._server = utils.connection_params()
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._alive = False
        self._buffer = b''
        self._id = client_id
        self.version = None
        self._guest_allowed = False
        self._accepted = False

    def alive(self):
        "Check if connection with the server is still alive"
        return self._alive

    def _handshake(self, data, user=None, password=None):
        "Shake hands with server"
        serv_error = data.get('error')
        if serv_error:
            raise exceptions.AuthError(utils.this_function(), serv_error)
        serv_data = data.get('data')
        if serv_data == "Authenticated":
            self._accepted = True
        elif serv_data:
            self._guest_allowed = serv_data.get('guest_allowed')
            self.version = serv_data.get('version')
            d = {}
            if user:
                d['user'] = user
                d['password'] = password
            self._send(message.finalize(d, name=self.name))
            self._handshake(self._recv())

    def connect(self, user=None, password=None):
        "Connect to the server"
        if not self._alive:
            try:
                self._sock.connect(self._server)
                self._alive = True
                self._handshake(self._recv(), user, password)
            except socket.error:
                raise exceptions.ClientError(
                    self.name, "Failed to establish server connection")

    def _send(self, msg_bytes):
        """
        Send bytes to server
        """
        log.d(
            "Sending",
            sys.getsizeof(msg_bytes),
            "bytes to server",
            self._server)
        if self._alive:
            self._sock.sendall(msg_bytes)
            self._sock.sendall(constants.postfix)
        else:
            raise exceptions.ServerDisconnectError(
                self.name, "Server already disconnected")

    def _recv(self):
        "returns json"
        try:
            buffered = None
            eof = False
            while not eof:
                temp = self._sock.recv(constants.data_size)
                if not temp:
                    self._alive = False
                    raise exceptions.ServerDisconnectError(
                        self.name, "Server disconnected")
                self._buffer += temp
                data, eof = utils.end_of_message(self._buffer)
                if eof:
                    buffered = data[0]
                    self._buffer = data[1]
            log.d(
                "Received",
                sys.getsizeof(buffered),
                "bytes from server",
                self._server)
            return utils.convert_to_json(buffered, self.name)
        except socket.error as e:
            # log disconnect
            self.alive = False
            raise exceptions.ServerError(self.name, "{}".format(e))

    def communicate(self, msg):
        """Send and receive data with server

        params:
            msg -- dict
        returns:
            dict from server
        """
        if not self._accepted:
            raise exceptions.AuthError(utils.this_function(), "")
        self._send(bytes(json.dumps(msg), 'utf-8'))
        return self._recv()

    def close(self):
        "Close connection with server"
        log.i("Closing connection to server")
        self._alive = False
        self._sock.close()
