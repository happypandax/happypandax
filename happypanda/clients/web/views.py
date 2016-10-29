from flask import render_template, flash, request, url_for, redirect, abort, g
from happypanda.common import constants
from happypanda.clients.web import happyweb

@happyweb.route('/')
def index():
    return render_template('index.html')


#import socket, time, random

#clientn = random.randint(1, 10)
#client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#client.connect(('localhost', 5577))

#while True:
#    print("Sending...")
#    client.sendall(bytearray("<xml>this is client {}</xml>".format(clientn), 'utf-8'))
#    client.sendall(b'end')
#    print("Receiving...")
#    print(client.recv(8192))
#    print("Sleeping...")
#    time.sleep(random.randint(1,5))

#client.close()

if __name__ == '__main__':
    happyweb.run(constants.host, constants.web_port)