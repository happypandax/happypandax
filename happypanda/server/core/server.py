import json

from gevent import socket, pool, queue
from gevent.server import StreamServer
from gevent.wsgi import WSGIServer

from happypanda.common import constants, exceptions, utils, message
from happypanda.server.core import interface, db
from happypanda.webclient import main as hweb

class ClientHandler:
    "Handles clients"
    def __init__(self, client, address, api=constants.version_api):
        self._client = client
        self._address = address
        self.api = api

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


class HPServer:
    "Happypanda Server"
    def __init__(self):
        params = utils.connectionParams()
        self._pool = pool.Pool(constants.client_limit)
        self._server = StreamServer(params, self._handle, spawn=self._pool)
        self._web_server = None
        self._clients = set()

    def _parse_client(self, json_data, client, address):
        "Parse first client message"
        print(json_data)
        return message.msg("Received")

    def _handle(self, client, address):
        "Client handle function"
        # log client connected
        print("Client connected")
        handler = None
        self._clients.add(client)
        # send server info
        ClientHandler.sendall(client, message.serverInfo())

        try:
            buffer = b''
            while True:
                if buffer.endswith(constants.postfix):
                    if handler:
                        handler.advance(buffer)
                    else:
                        handler = self._parse_client(buffer, client, address)
                        if not handler:
                            # inform client
                            # log
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
            self._clients.remove(client)

    def _start(self, blocking=True):
        
        # TODO: handle db errors

        db.init()

        try:
            if blocking:
                self._server.serve_forever()
            else:
                self._server.start()
        except socket.error as e:
            # log error
            utils.eprint("Error: Failed to start server (Port might already be in use)") # include

    def run(self, web=False, interactive=False):
        "Run the server forever, blocking"
        if web:
            # start webserver
            try:
                hweb.socketio.run(hweb.happyweb, *utils.connectionParams(web=True), block=False)
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