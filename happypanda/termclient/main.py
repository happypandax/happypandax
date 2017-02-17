"A command line client"
import socket

from happypanda.common import constants

client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
host = socket.gethostname()
client.connect((host, constants.local_port))
client.send(e)
client.shutdown(socket.SHUT_RDWR)
client.close()