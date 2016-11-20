from lxml import etree

import sys
import socket
import time
import random

from happypanda.common import constants, exceptions

def eprint(*args, **kwargs):
    "Prints to stderr"
    print(*args, file=sys.stderr, **kwargs)

def connectionParams(web=False):
    "Retrieve host and port"
    if web:
        params = (constants.host, constants.web_port)
        return params
    else:
        if constants.public_server:
            # TODO: finish this
            # Note: upnpc
            raise NotImplementedError
        else:
            params = (constants.host, constants.local_port)
        return params

## SERVER ##
class Client:
    """A common wrapper for communicating with server.

    Params:
        name -- name of client
    """

    def __init__(self, name):
        self.name = name
        self._server = (constants.host, constants.local_port)
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._alive = False
        self._versions = {}

    def alive(self):
        "Check if connection with the server is still alive"
        return self._alive

    def _connect(self):
        "Connect to the server"
        if not self._alive:
            try:
                self._sock.connect(self._server)
                self._alive = True
                # receive versions
                for v in self._recv():
                    self._versions[v.get("name")] = v.text
            except socket.error:
                raise exceptions.ClientError(self.name, "Failed to establish server connection")

    def _recv(self):
        ""
        # log receive
        try:
            buffer = b''
            while not buffer.endswith(constants.postfix): # loose
                data = self._sock.recv(constants.data_size)
                if not data:
                    self._alive = False
                    raise exceptions.ServerDisconnectError(self.name, "Server disconnected")
                buffer += data
            # log received
            try:
                xml_data = etree.XML(buffer[:-len(constants.postfix)]) # slice 'end' off
            except etree.XMLSyntaxError as e:
                raise exceptions.XMLParseError(buffer, self.name, "Failed parsing xml data: {}".format(e))
            return xml_data
        except socket.error as e:
            # log disconnect
            self.alive = False
            raise exceptions.ServerError(self.name, "{}".format(e))

    def communicate(self, xmlmsg):
        """Send and receive data with server

        params:
            xmlmsg -- etree._Element
        returns:
            etree._Element
        """
        # log send
        if self._alive:
            if isinstance(xmlmsg, etree._Element):
                self._sock.sendall(xmlmsg)
                self._sock.sendall(constants.postfix)
            else:
                raise exceptions.ClientError(self.name, "xmlmsg must be an etree._Element")
            return self._recv()
        else:
            raise exceptions.ServerDisconnectError(self.name, "Server already disconnected")

    def close(self):
        "Close connection with server"
        self._alive = False
        self._sock.close()

