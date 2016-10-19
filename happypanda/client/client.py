import socket, time, random

clientn = random.randint(1, 10)
client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client.connect(('localhost', 5577))

while True:
    client.sendall(bytearray("this is client {}".format(clientn), 'utf-8'))
    time.sleep(random.randint(1,5))

client.close()
