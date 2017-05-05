import json
import uuid
import logging
import sys

from inspect import getmembers, isfunction
from collections import deque
from enum import Enum

from gevent import socket, pool, queue
from gevent.server import StreamServer

from happypanda.common import constants, exceptions, utils, message
from happypanda.server import interface
from happypanda.server.core import db
from happypanda.webclient import main as hweb

log = utils.Logger(__name__)

def list_api():
    ""
    _special_functions = ('interactive',) # functions we don't consider as part of the api
    all_functions = []
    mods = utils.get_package_modules(interface)
    for m in mods:
        all_functions.extend(getmembers(m, isfunction))
    return {x[0] : x[1] for x in all_functions if not x[0] in _special_functions}

class Errors:
    "Error system"

    class Severity(Enum):
        Low = 0
        High = 1

    def __init__(self):
        self.errors = deque()

    def add_error(self, exception, severity):
        assert isinstance(exception, exceptions.CoreError)
        assert isinstance(severity, Severity)

        if severity == Severity.Low:
            self.errors.appendleft(exception)
        elif severity == Severity.High:
            self.errors.append(exception)


    def get_error(self):
        if not self.errors:
            return None
        return self.errors.pop()


class ClientHandler:
    "Handles clients"

    api = list_api() # {name : object}

    def __init__(self, client, address):
        self._client = client
        self._address = address
        self._stopped = False
        self.context = None
        self.errors = Errors()
        self.get_context()
        self.context.errors = self.errors

    def get_context(self):
        "Creates or retrieves existing context object for this client"
        s = constants.db_session()
        self.context = s.query(db.User).filter(db.User.address == self._address[0]).one_or_none()
        if not self.context:
            self.context = db.User()
            self.context.address = self._address[0]
            self.context.context_id = uuid.uuid4().hex
            s.add(self.context)
            s.commit()

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
        
        log.d("Sending", sys.getsizeof(msg), "bytes to", client)
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
            list of (function, function_kwargs, context_neccesity)
        """
        where = "Message parsing"
        log.d("Parsing incoming data")
        j_data = utils.convert_to_json(data, where)

        log.d("Check if required root keys are present")
        # {"name":name, "data":data}
        root_keys = ('name', 'data')
        self._check_both(where, "JSON dict", root_keys, j_data)
               
        # 'data': [ list of function dicts ]
        function_keys = ('fname',)
        msg_data = j_data['data']
        if isinstance(msg_data, list):
            function_tuples = []
            for f in msg_data:
                log.d("Cheking parameters in:", f)
                self._check_missing(where, "Function message", function_keys, f)

                function_name = f['fname']
                # check function
                if not function_name in self.api:
                    raise exceptions.InvalidMessage(where, "Function not found: '{}'".format(function_name))

                # check parameters
                func_args = tuple(arg for arg in f if not arg in function_keys)
                func_varnames = self.api[function_name].__code__.co_varnames
                need_ctx = 'ctx' in func_varnames
                for arg in func_args:
                    if not arg in func_varnames:
                        raise exceptions.InvalidMessage(where,"Unexpected argument in function '{}': '{}'".format(
                            function_name,
                            arg))

                function_tuples.append((self.api[function_name], {x: f[x] for x in func_args}, need_ctx))

            return function_tuples
        else:
            raise exceptions.InvalidMessage(where, "No list of function objects found in 'data'")

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
            if constants.server_ready:
                function_list = message.List("function", message.Function)
                functions = self.parse(buffer)
                for func, func_args, ctx in functions:
                    log.d("Calling function", func, "with args", func_args)
                    if ctx:
                        func_args['ctx'] = self.context
                        msg = func(**func_args)
                    else:
                        msg = func(**func_args)
                    assert isinstance(msg, message.CoreMessage)
                    function_list.append(message.Function(func.__name__, msg))
                self.send(function_list.serialize())
            else:
                self.on_wait()
        except exceptions.CoreError as e:
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
        assert isinstance(exception, exceptions.CoreError)
        e = message.Error(exception.code, exception.msg)
        self.send(e.serialize())

    def on_wait(self):
        """
        Sends wait message to client
        """
        self.send(message.Message("wait").serialize())

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
        log.d("Client connected", str(client), str(address))
        handler = ClientHandler(client, address)
        self._clients.add(handler)
        try:
            buffer = b''
            while True:
                data, eof = utils.end_of_message(buffer)
                #log.d("EOF:", eof, "Data:", data)
                if eof:
                    buffer = data[1]
                    if handler.is_active():
                        handler.advance(data[0])
                    else:
                        # log client disconnected
                        break
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
        log.d("Client disconnected", str(client), str(address))

    def _start(self, blocking=True):
        # TODO: handle db errors

        db.init()

        try:
            if blocking:
                print("Starting server... (Port: {}) (blocking)".format(constants.local_port))
                self._server.serve_forever()
            else:
                self._server.start()
                print("Server successfully started (Port: {})".format(constants.local_port))
        except (socket.error, OSError) as e:
            # log error
            utils.eprint("Error: Failed to start server (Port might already be in use)") # include e

    def run(self, web=False, interactive=False):
        """Run the server forever, blocking
        Params:
            web -- Start the web server
            interactive -- Start in interactive mode (Note: Does not work with web server)
        """
        self._start(not (web or interactive))

        if web:
            # start webserver
            try:
                print("Web server successfully starting... (Port: {}) {}".format(constants.web_port, "(blocking)" if not interactive else ""))
                # OBS: will trigger a harmless socket.error when debug=True (stuff still works)
                hweb.socketio.run(hweb.happyweb, *utils.connection_params(web=True), block=not interactive, debug=constants.debug)
                # log
                print("Web server successfully started (Port: {})".format(constants.web_port))
            except (socket.error, OSError) as e:
                # log error
                utils.eprint("Error: Failed to start web server (Port might already be in use)") #include e
        

        if interactive:
            interface.interactive()

        # log server shutduown
        print("Server shutting down.")

if __name__ == '__main__':
    server = HPServer()
    server.run()