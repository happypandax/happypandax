from gevent import socket, pool, queue
from gevent.server import StreamServer

from happypanda.common import constants, exceptions

class HPServer:
    ""
    def __init__(self):
        if constants.public_server:
            params = (socket.gethostname(), constants.public_port)
        else:
            params = (constants.host, constants.local_port)
        self._pool = pool.Pool(constants.client_limit)
        self._server = StreamServer(params, self._handle, spawn=self._pool)
        self._clients = set()

    def parse(self, xml_data):
        "Parse message in XML format"
        print(xml_data)
        return b'<xml>Received</xml>'

    def _handle(self, client, address):
        # log client connected
        print("Client connected")
        self._clients.add(client)
        client.sendall(b"Welcome")
        try:
            buffer = b''
            while True:
                if buffer.endswith(b'end'):
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
            # log errpr
            print("Client disconnected", e)
        finally:
            self._clients.remove(client)

    def run(self):
        "Start the server"
        try:
            self._server.serve_forever()
        except socket.error as e:
            # log error
            print("Error: Port might already be in use")




if __name__ == '__main__':
    server = HPServer()
    server.run()