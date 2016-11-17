from lxml import etree

import sys
import socket
import time
import random

from happypanda.common import constants, exceptions

def eprint(*args, **kwargs):
    "Prints to stderr"
    print(*args, file=sys.stderr, **kwargs)

## SERVER ##
class Client:
    "A common wrapper for communicating with server"

    def __init__(self, name):
        "name -- name of client"
        self.name = name
        self._server = (constants.host, constants.local_port)
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._connect()

    def _connect(self):
        try:
            self._sock.connect(self._server)
        except socket.error:
            raise exceptions.ClientError(self.name, "Could not establish server connection")

    def _communicate(self, xmlmsg):
        """Send and receive data with server

        params:
            xmlmsg -- etree._Element
        returns:
            etree._Element
        """
        try:
            # log send
            if isinstance(xmlmsg, etree._Element):
                self._sock.sendall(xmlmsg)
            else:
                raise exceptions.ClientError(self.name, "xmlmsg must be an etree._Element")
            self._sock.sendall(constants.postfix)
            # log receive
            buffer = b''
            if not buffer.endswith(constants.postfix):
                data = self._sock.recv(constants.data_size)
                if not data:
                    raise exceptions.ServerDisconnectError(self.name, "Server disconnected")
                buffer += data
            # log received
            try:
                xml_data = etree.XML(buffer[:-len(constants.postfix)]) # slice 'end' off
            except etree.XMLSyntaxError as e:
                raise exceptions.XMLParseError(xml_data, self.name, "Failed parsing xml data: {}".format(e))
            return xml_data
        except socket.error as e:
            # log disconnect
            raise exceptions.ServerError(self.name, "{}".format(e))


    def close(self):
        "Close connection with server"
        self._sock.close()

#while True:
#    print("Sending...")
#    client.sendall(bytearray("<xml>this is client {}</xml>".format(clientn), 'utf-8'))
#    client.sendall(b'end')
#    print("Receiving...")
#    print(client.recv(8192))
#    print("Sleeping...")
#    time.sleep(random.randint(1,5))

#client.close()


