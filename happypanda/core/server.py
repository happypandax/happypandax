from gevent import socket, pool
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

    def parse(self, xml_data):
        "Parse message in XML format"
        print(xml_data)
        return b'<xml>Received</xml>'

    def _handle(self, client, address):
        # log client connected
        client.sendall("Welcome")
        try:
            buffer = b''
            rclient = client.makefile(mode='rb')
            while True:
                line = rclient.readline()
                if not line:
                    # log client disconnected
                    break
                if line.lower.strip() == b'end':
                    d = parse(buffer)
                    client.sendall(d)
                    client.sendall(b'end')
                    buffer = b''
                else:
                    buffer += line
        except socket.error as e:
            # log errpr
            print(e)
        finally:
            rclient.close()

    def run(self):
        "Start the server"
        self._server.serve_forever()




if __name__ == '__main__':
    server = HPServer()
    server.run()