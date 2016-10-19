import socket
import select
import queue
import threading

from happypanda.common import constants, exceptions


clients = set()

class ClientManager(threading.Thread):
    "Manages clients"
    def __init__(self, iqueue, oqueue):
        super().__init__()
        self.iqueue = iqueue
        self.oqueue = oqueue
        self.client_buffer = {}

    def handleClient(self, client, data):
        pass

    def sendToClient(self,):
        pass

    def processInput(self):
        try:
            client, data = self.iqueue.get_nowait()
        except queue.Empty:
            return
        else:
            if not client in self.client_buffer:
                self.client_buffer[client] = b''
            if b'end' in data:
                self.handleClient(client, self.client_buffer[client])
                self.client_buffer[client] = b''
            else:
                self.client_buffer[client] += data

    def processOutput(self):
        pass

    def run(self):
        while constants.status:
            self.processInput()

def disconnectClient(client):
    client.close()
    clients.remove(client)
    # log remove?

def startServer():

    hpserver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if constants.public_server:
        hpserver.bind((socket.gethostname(), constants.public_port))
    else:
        hpserver.bind((constants.host, constants.local_port))
    hpserver.listen(constants.connections)
    clients.add(hpserver)

    iqueue = queue.Queue()
    oqueue = queue.Queue()
    manager = ClientManager(iqueue, oqueue)
    manager.start()


    print("Started server")
    while constants.status:
        try:
            ready_odata = oqueue.get_nowait()
        except queue.Empty:
            ready_odata = {}

        readers, writers, errors = select.select(clients, ready_odata.keys(), clients)

        for client in readers:
            if client == hpserver:
                new_client, address = hpserver.accept()
                # log address
                new_client.setblocking(0)
                clients.add(new_client)
            else:
                try:
                    client_data = client.recv(constants.data_size)
                except socket.error:
                    client_data = b""
                    # log error

                if client_data:
                   iqueue.put((client, client_data))
                else:
                    disconnectClient(client)

        for client in writers:
            next_data = ready_odata[client]
            try:
                client.sendall(next_data)
            except socket.error:
                pass
                # log error

        for client in errors:
            # log that an error occured with this client, client.getpeername()
            disconnectClient(client)


if __name__ == '__main__':
    startServer()