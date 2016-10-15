import socket
import select

from happypanda.common import constants, exceptions

hpserver = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
hpserver.bind(constants.host, constants.port)
hpserver.listen(constants.connections)

clients = [hpserver]
buffer_idata = {}
buffer_odata = {}

def startServer():
    while True:
        iready, oready, eready = select.select(clients, buffer_odata.keys(), [])

        for client in iready:
            if client == hpserver:
                new_client, address = hpserver.accept()
                clients.append(new_client)
                # log address

            else:
                try:
                    clent_data = client.recv(constants.data_size)
                except socket.error:
                    client_data = b""

                if client_data:
                    pass
                else:
                    client.close()
                    clients.remove(client)
                    for b in (buffer_idata, buffer_odata):
                        if cleint in b:
                            del b[client]

        for client in oready:
            if not client in buffer_odata:
                continue
