import json

from inspect import getmembers, isfunction

from gevent import socket, pool, queue
from gevent.server import StreamServer
from gevent.wsgi import WSGIServer

from happypanda.common import constants, exceptions, utils, message
from happypanda.server.core import interface, db
from happypanda.webclient import main as hweb

class ClientHandler:
    "Handles clients"

    api = [x for x in getmembers(interface, isfunction)] # lsit of tuples: (name, function)

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

    def parse(self, data):
        """
        Parse data from client
        Params:
            data -- data from client
        """
        pass

    def advance(self, buffer):
        """
        Advance the loop for this client
        Params:
            buffer -- data buffer to be parsed
        """
        pass

    def is_active(self):
        """
        Return bool indicating status of client
        """
        return not self._stopped


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
        # send server info
        ClientHandler.sendall(client, message.server_info())

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
                print("Starting server...")
                self._server.serve_forever()
            else:
                self._server.start()
                print("Server successfully started")
        except socket.error as e:
            # log error
            utils.eprint("Error: Failed to start server (Port might already be in use)") # include e

    def run(self, web=False, interactive=False):
        "Run the server forever, blocking"
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
            #interface.interactive()  # doesnt work yet
        else:
            self._start()

        # log server shutduown
        print("Server shutting down.")

if __name__ == '__main__':
    server = HPServer()
    server.run()