import socket
import logging
import sys

from happypanda.common import constants, exceptions, utils, message

log = utils.Logger(__name__)

def call_on_server(client, func_name, **kwargs):
    """Call function on server
    Params:
        client -- A Client instance
        func_name -- name of function
        **kwargs -- additional function arguments
    Returns:
        whatever message was returned by the function
    """
    assert isinstance(client, Client)
    assert isinstance(func_name, str)
    log.d("Calling function on server:", func_name, "with kwargs: {}".format(kwargs))
    func_list = message.List("function", FunctionInvoke)
    func_list.append(FunctionInvoke(func_name, **kwargs))
    data = client.communicate(func_list)
    error = None
    func_data = {}
    if 'data' in data:
        for f in data['data']:
            func_data[f['fname']] = {'data': f['data']}
            if 'error' in f:
                func_data[f['f_name']]['error'] = f['error']
    else:
        pass # error out

    if 'error' in data:
        error = data['error']
    return func_data, error

def extract_data(json_data):
    ""
    pass

def error_handler(error):
    pass

class Client:
    """A common wrapper for communicating with server.

    Params:
        name -- name of client
    """

    def __init__(self, name):
        self.name = name
        self._server = utils.connection_params()
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._alive = False
        self._buffer = b''

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
            buffered = None
            eof = False
            while not eof:
                temp = self._sock.recv(constants.data_size)
                if not temp:
                    self._alive = False
                    raise exceptions.ServerDisconnectError(self.name, "Server disconnected")
                self._buffer += temp
                data, eof = utils.end_of_message(self._buffer)
                if eof:
                    buffered = data[0]
                    self._buffer = data[1]
            log.d("Received", sys.getsizeof(buffered), "bytes from server")
            return utils.convert_to_json(buffered, self.name)
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

        log.d("Sending", sys.getsizeof(msg), "bytes to server")
        if self._alive:
            self._sock.sendall(msg.serialize(self.name))
            self._sock.sendall(constants.postfix)
            return self._recv()
        else:
            raise exceptions.ServerDisconnectError(self.name, "Server already disconnected")

    def close(self):
        "Close connection with server"
        log.i("Closing connection to server")
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

