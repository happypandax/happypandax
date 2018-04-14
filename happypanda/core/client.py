import socket
import sys
import json
import errno
import gzip

from happypanda.common import constants, exceptions, utils, hlogger, config
from happypanda.core import message

log = hlogger.Logger(constants.log_ns_client + __name__)


class Client:
    """A common wrapper for communicating with server.

    Params:
        name -- name of client
    """

    def __init__(self, name, session_id="", client_id=""):
        self.id = client_id
        self.name = name
        # HACK: properly fix this
        self._server = utils.get_qualified_name(config.host.value, config.port.value).split(':')
        self._server = (self._server[0], int(self._server[1]))
        if config.enable_ssl.value is True or config.enable_ssl.value == "server":
            self._context = utils.create_ssl_context()
            self._sock = self._context.wrap_socket(socket.socket(socket.AF_INET, socket.SOCK_STREAM))
        else:
            self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._alive = False
        self._buffer = b''
        self.session = session_id
        self.version = None
        self.guest_allowed = False
        self._accepted = False

        self._last_user = ""
        self._last_pass = ""

        self.timeout = 10

    def alive(self):
        "Check if connection with the server is still alive"
        return self._alive

    def _server_info(self, data):
        if data:
            serv_data = data.get('data')
            if serv_data and "version" in serv_data:
                self.guest_allowed = serv_data.get('guest_allowed')
                self.version = serv_data.get('version')

    def handshake(self, data={}, user=None, password=None, ignore_err=False):
        "Shake hands with server"
        if self.alive():
            if user:
                self._last_user = user
                self._last_pass = password
            if not ignore_err and data:
                serv_error = data.get('error')
                if serv_error:
                    if serv_error['code'] == exceptions.AuthWrongCredentialsError.code:
                        raise exceptions.AuthWrongCredentialsError(utils.this_function(), serv_error['msg'])
                    elif serv_error['code'] == exceptions.AuthRequiredError.code:
                        raise exceptions.AuthRequiredError(utils.this_function(), serv_error['msg'])
                    elif serv_error['code'] == exceptions.AuthMissingCredentials.code:
                        raise exceptions.AuthMissingCredentials(utils.this_function(), serv_error['msg'])
                    else:
                        raise exceptions.AuthError(
                            utils.this_function(), "{}: {}".format(
                                serv_error['code'], serv_error['msg']))
            if not data:
                d = {}
                if user:
                    d['user'] = user
                    d['password'] = password
                self._send(message.finalize(d, name=self.name))
                self.handshake(self._recv(), ignore_err=ignore_err)
            elif data:
                serv_data = data.get('data')
                if serv_data == "Authenticated":
                    self.session = data.get('session')
                    self._accepted = True

    def request_auth(self, ignore_err=False):
        self._server_info(self.communicate({'session': "", 'name': self.name,
                                            'data': 'requestauth'}, True))
        self.handshake(user=self._last_user, password=self._last_pass, ignore_err=ignore_err)

    def connect(self):
        "Connect to the server"
        if not self._alive:
            try:
                log.i("Client connecting to server at: {}".format(self._server))
                try:
                    self._sock.connect(self._server)
                except (OSError, ConnectionError) as e:
                    if e.errno == errno.EISCONN and self.session:  # already connected
                        self._alive = True
                        return
                    else:
                        raise
                self._alive = True
                self._server_info(self._recv())
                if self.session:
                    self._accepted = True
            except (OSError, ConnectionError) as e:
                self._disconnect()
                raise exceptions.ServerDisconnectError(
                    self.name, "{}".format(e))

    def _disconnect(self):
        self._alive = False
        self._accepted = False
        self.session = ""

    def _send(self, msg_bytes):
        """
        Send bytes to server
        """
        if not self._alive:
            raise exceptions.ClientError(self.name, "Client '{}' is not connected to server".format(self.name))

        log.d(
            "Sending",
            sys.getsizeof(msg_bytes),
            "bytes to server",
            self._server)
        try:
            self._sock.sendall(gzip.compress(msg_bytes, 5))
            self._sock.sendall(constants.postfix)
        except socket.error as e:
            self._disconnect()
            raise exceptions.ClientError(self.name, "{}".format(e))

    def _recv(self):
        "returns json"
        try:
            buffered = None
            eof = False
            while not eof:
                temp = self._sock.recv(constants.data_size)
                if not temp:
                    self._disconnect()
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
            buffered = gzip.decompress(buffered)
            return utils.convert_to_json(buffered, self.name, log=log)
        except socket.error as e:
            self._disconnect()
            raise exceptions.ServerError(self.name, "{}".format(e))

    def communicate(self, msg, auth=False):
        """Send and receive data with server

        params:
            msg -- dict
        returns:
            dict from server
        """
        if self._alive and not self._accepted and not auth:
            raise exceptions.AuthRequiredError(utils.this_function(),
                                               "Client '{}' is connected but not authenticated".format(self.name))
        self._send(bytes(json.dumps(msg), 'utf-8'))
        return self._recv()

    def close(self):
        "Close connection with server"
        log.i("Closing connection to server")
        self._disconnect()
        self._sock.close()
