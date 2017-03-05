import json

from inspect import getmembers, isfunction

from gevent import socket, pool, queue
from gevent.server import StreamServer
from gevent.wsgi import WSGIServer

from happypanda.common import constants, exceptions, utils, message
from happypanda.server.core import interface, db
from happypanda.webclient import main as hweb

_special_functions = ('interactive',) # functions we don't consider as part of the api

class ClientHandler:
    "Handles clients"

    api = {x[0] : x[1] for x in getmembers(interface, isfunction) if not x[0] in _special_functions} # {name : object}

    def __init__(self, client, address):
        self._client = client
        self._address = address
        self._stopped = False

    @staticmethod
    def sendall(client, msg):
        """
        Send data to client
        Params:
            client -- 
            msg -- bytes
        """
        #assert isinstance(client, ...)
        assert isinstance(msg, bytes) 

        client.sendall(msg)
        client.sendall(constants.postfix)

    def send(self, msg):
        """
        Wraps sendall
        """
        ClientHandler.sendall(self._client, msg)

    def parse(self, data):
        """
        Parse data from client
        Params:
            data -- data from client
        Returns:
            list of (function, function_kwargs)
        """
        where = "Message parsing"
        # TODO: log
        try:
            j_data = json.loads(data.decode())
            # {"name":name, "data":data}
            root_keys = ('name', 'data')
            self._check_both(where, "JSON dict", root_keys, j_data)
               
            # 'data': [ list of function dicts ]
            function_keys = ('name',)
            msg_data = j_data['data'],
            if isinstance(msg_data, list):
                function_tuple = []
                for f in msg_data:
                    self._check_missing(where, "Function message", function_keys, f)

                    function_name = f['name']
                    # check function
                    if not function_name in self.api:
                        raise exceptions.InvalidMessage(where, "Function not found: '{}'".format(function_name))

                    # check parameters
                    func_args = tuple(arg for arg in f if not arg in function_keys)
                    for arg in func_args:
                        if not arg in self.api[function_name].__code__.co_varnames:
                            raise exceptions.InvalidMessage(where,"Unexpected argument in function '{}': '{}'".format(function_name,
                                arg))

                    function_tuple.append((self.api[function_name], {x: f[x] for x in func_args}))

                return function_tuple
            else:
                raise exceptions.InvalidMessage(where, "No list of function objects found in 'data'")

        except json.JSONDecodeError as e:
            raise exceptions.JSONParseError(data, constants.server_name, "{}".format(e.msg))

    def _check_both(self, where, msg, keys, data):
        "Invokes both missing and unknown key"
        self._check_missing(where, msg, keys, data)
        self._check_unknown(where, msg, keys, data)

    def _check_unknown(self, where, msg, keys, data):
        "Checks if there are unknown keys in provided data"
        if len(data) != len(keys):
            self._check_required_key(where, "{} contains unknown key '{}'".format(msg, "{}"), keys, data)

    def _expect_iterable(self, where, data):
        if not isinstance(data, (list, dict, tuple)):
            raise exceptions.InvalidMessage(where, "A list/dict was expected, not: {}".format(data))

    def _check_missing(self, where, msg, keys, data):
        "Check if required keys are missing in provided data"
        self._check_required_key(where, "{} missing '{}' key".format(msg, "{}"), data, keys)

    def _check_required_key(self, where, msg, required_keys, data):
        ""
        for y in (required_keys, data):
            self._expect_iterable(where, y)
        for x in data:
            if not x in required_keys:
                raise exceptions.InvalidMessage(where, msg.format(x))

    def advance(self, buffer):
        """
        Advance the loop for this client
        Params:
            buffer -- data buffer to be parsed
        """
        try:
            func, func_args = self.parse(buffer)
            

        except exceptions.ServerError as e:
            self.on_error(e)

    def is_active(self):
        """
        Return bool indicating status of client
        """
        return not self._stopped

    def on_error(self, exception):
        """
        Creates and sends error message to client
        """
        pass


class HPServer:
    "Happypanda Server"
    def __init__(self):
        params = utils.connection_params()
        self._pool = pool.Pool(constants.client_limit)
        self._server = StreamServer(params, self._handle, spawn=self._pool)
        self._web_server = None
        self._clients = set() # a set of client handlers

    def _handle(self, client, address):
        "Client handle function"
        # log client connected
        print("Client connected")
        handler = ClientHandler(client, address)
        self._clients.add(handler)
        try:
            buffer = b''
            while True:
                if buffer.endswith(constants.postfix):
                    if handler.is_active():
                        handler.advance(buffer)
                    else:
                        # log client disconnected
                        break
                    buffer = b''
                r = client.recv(constants.data_size)
                if not r:
                    # log client disconnected
                    break
                else:
                    buffer += r
        except socket.error as e:
            # log error
            utils.eprint("Client disconnected", e)
        finally:
            self._clients.remove(handler)
        print(client, " disconnected")

    def _start(self, blocking=True):
        # TODO: handle db errors

        db.init()

        try:
            if blocking:
                print("Starting server... (blocking)")
                self._server.serve_forever()
            else:
                self._server.start()
                print("Server successfully started")
        except socket.error as e:
            # log error
            utils.eprint("Error: Failed to start server (Port might already be in use)") # include e

    def run(self, web=False, interactive=False):
        """Run the server forever, blocking
        Params:
            web -- Start the web server
            interactive -- Start in interactive mode
        """
        if web:
            # start webserver
            try:
                hweb.socketio.run(hweb.happyweb, *utils.connection_params(web=True), block=False)
                # log
                print("Web server successfully started")
            except socket.error as e:
                # log error
                utils.eprint("Error: Failed to start web server (Port might already be in use)") #include e
        

        if interactive:
            self._start(False)
            interface.interactive()
        else:
            self._start()

        # log server shutduown
        print("Server shutting down.")

if __name__ == '__main__':
    server = HPServer()
    server.run()