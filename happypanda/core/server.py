from lxml import etree
from lxml.builder import E

from gevent import socket, pool, queue
from gevent.server import StreamServer
from gevent.wsgi import WSGIServer

from happypanda.common import constants, exceptions, utils, message
from happypanda.core import interface
from happypanda.clients.web import main as hweb

class HPServer:
    "Happypanda Server"
    def __init__(self):
        params = utils.connectionParams()
        self._pool = pool.Pool(constants.client_limit)
        self._server = StreamServer(params, self._handle, spawn=self._pool)
        self._web_server = None
        self._clients = set()

    def parse(self, xml_data):
        "Parse message in XML format"
        print(xml_data)
        return message.msg("Received")

    def _handle(self, client, address):
        "Client handle function"
        # log client connected
        print("Client connected")
        self._clients.add(client)
        # send server info
        client.sendall(message.serverInfo())
        client.sendall(constants.postfix)
        try:
            buffer = b''
            while True:
                if buffer.endswith(constants.postfix):
                    d = self.parse(buffer)
                    client.sendall(d)
                    client.sendall(constants.postfix)
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

    def run(self, web=False):
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
                
        try:
            self._server.serve_forever()
        except socket.error as e:
            # log error
            utils.eprint("Error: Failed to start server (Port might already be in use)") # include e
        # log server shutduown
        print("Server shutting down.")

if __name__ == '__main__':
    server = HPServer()
    server.run()