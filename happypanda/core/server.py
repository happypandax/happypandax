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
        self.data_length = {}

    def sendToClient(self,):
        pass

    def processInput(self):
        try:
            next_data = self.iqueue.get_nowait()
        except queue.Empty:
            return
        else:
            pass

    def processOutput(self):
        pass

    def run(self):
        while constants.status:
            self.processInput()
            self.processOutput()

def disconnectClient(client):
    client.close()
    clients.remove(client)
    # log remove?

def startServer():
    hpserver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    if constants.public_server:
        hpserver.bind((socket.gethostname(), constants.public_port))
    else:
        hpserver.bind(constants.host, constants.local_port)
    hpserver.listen(constants.connections)
    clients.add(hpserver)

    iqueue = queue.Queue()
    oqueue = queue.Queue()
    manager = ClientManager(iqueue, oqueue)
    manager.start()


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
                    clent_data = client.recv(constants.data_size)
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
