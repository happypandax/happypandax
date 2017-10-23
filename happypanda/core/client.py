import socket
import sys
import json

from happypanda.common import constants, exceptions, utils, hlogger, config
from happypanda.core import message

log = hlogger.Logger(__name__)


class Client:
    """A common wrapper for communicating with server.

    Params:
        name -- name of client
    """

    def __init__(self, name, session_id="", client_id=""):
        self.id = client_id
        self.name = name
        # HACK: properly fix this
        host = config.host.value
        if isinstance(host, str):
            host = "localhost" if host.lower() == "0.0.0.0" else host
        self._server = (host, config.port.value)
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._alive = False
        self._buffer = b''
        self.session = session_id
        self.version = None
        self._guest_allowed = False
        self._accepted = False

        self._last_user = ""
        self._last_pass = ""

    def alive(self):
        "Check if connection with the server is still alive"
        return self._alive

    def _handshake(self, data, user=None, password=None, ignore_err=False):
        "Shake hands with server"
        if not ignore_err:
            serv_error = data.get('error')
            if serv_error:
                raise exceptions.AuthError(utils.this_function(), serv_error)
        serv_data = data.get('data')
        if serv_data == "Authenticated":
            self.session = data.get('session')
            self._accepted = True
        elif serv_data and "version" in serv_data:
            self._guest_allowed = serv_data.get('guest_allowed')
            self.version = serv_data.get('version')
            d = {}
            if user:
                d['user'] = user
                d['password'] = password
            self._send(message.finalize(d, name=self.name))
            self._handshake(self._recv())

    def request_auth(self):
        self._handshake(self.communicate({'session': "", 'name': self.name,
                                          'data': 'requestauth'}, True), self._last_user, self._last_pass)

    def connect(self, user=None, password=None):
        "Connect to the server"
        if not self._alive:
            self._last_user = user
            self._last_pass = password
            try:
                log.i("Client connecting to server at: {}".format(self._server))
                self._sock.connect(self._server)
                self._alive = True
                if not self.session:
                    self._handshake(self._recv(), user, password)
                else:
                    self._accepted = True
                    self._recv()
            except socket.error:
                self.session = ""
                raise exceptions.ClientError(
                    self.name, "Failed to establish server connection")

    def _send(self, msg_bytes):
        """
        Send bytes to server
        """
        if not self._alive:
            raise exceptions.ClientError(self.name, "Client is not connected to server")
        log.d(
            "Sending",
            sys.getsizeof(msg_bytes),
            "bytes to server",
            self._server)
        try:
            self._sock.sendall(msg_bytes)
        except ConnectionError:
            self.session = ""
        self._sock.sendall(constants.postfix)

    def _recv(self):
        "returns json"
        try:
            buffered = None
            eof = False
            while not eof:
                temp = self._sock.recv(constants.data_size)
                if not temp:
                    self._alive = False
                    self.session = ""
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
            self.session = ""
            raise exceptions.ServerError(self.name, "{}".format(e))

    def communicate(self, msg, auth=False):
        """Send and receive data with server

        params:
            msg -- dict
        returns:
            dict from server
        """
        if self.alive and not self._accepted and not auth:
            raise exceptions.AuthError(utils.this_function(), "Client is connected but not authenticated")
        self._send(bytes(json.dumps(msg), 'utf-8'))
        return self._recv()

    def close(self):
        "Close connection with server"
        log.i("Closing connection to server")
        self._alive = False
        self._sock.close()
