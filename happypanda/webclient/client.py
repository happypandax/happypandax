import socket

from happypanda.common import constants, exceptions, utils, message

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

    def alive(self):
        "Check if connection with the server is still alive"
        return self._alive

    def connect(self):
        "Connect to the server"
        if not self._alive:
            try:
                self._sock.connect(self._server)
                self._alive = True
            except socket.error:
                raise exceptions.ClientError(self.name, "Failed to establish server connection")

    def _recv(self):
        "returns json"
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
            return utils.convert_to_json(buffer, self.name)
        except socket.error as e:
            # log disconnect
            self.alive = False
            raise exceptions.ServerError(self.name, "{}".format(e))

    def communicate(self, msg):
        """Send and receive data with server

        params:
            msg -- Message object
        returns:
            json from server
        """
        assert isinstance(msg, message.CoreMessage)

        # log send
        if self._alive:
            self._sock.sendall(msg.serialize())
            self._sock.sendall(constants.postfix)
            return self._recv()
        else:
            raise exceptions.ServerDisconnectError(self.name, "Server already disconnected")

    def close(self):
        "Close connection with server"
        self._alive = False
        self._sock.close()


class FunctionInvoke(message.CoreMessage):
    "A function invoker message"

    def __init__(self, fname, **kwargs):
        super().__init__('function')
        assert isinstance(fname, str)
        self.name = fname
        self._kwargs = kwargs

    def add_kwargs(self, **kwargs):
        ""
        self._kwargs.update(kwargs)

    def data(self):
        d = {'fname':self.name}
        d.update(self._kwargs)
        return d

