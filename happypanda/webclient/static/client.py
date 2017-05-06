__pragma__ ('alias', 'S', '$') # JQuery

class Base:
    pass

class Client(Base):

    def __init__(self):
        self.socket = io.connect()
        self.socket.on("connection", self.on_connect)
        self.socket.on("response", self.on_response)

        self._disconnected_once = False
        self._connection_status = True
        self._response_cb = []

    def reconnect(self):
        def rc():
            if self._connection_status:
                clearInterval(con_interval)
                return
            self.socket.connect()
        con_interval = setInterval(rc, 5000)

    def on_response(self, msg):
        if self._response_cb:
            self._response_cb.pop(0)(msg)

    def on_connect(self, msg):
        self._connection_status = msg['status']
        con_text = "server connection: "
        text = "Connected" if self._connection_status else "Disconnected"
        con_text += text
        el = S("#serverstat")
        el.text(con_text)
        if self._connection_status:
            if self._disconnected_once:
                S("#global").append("<div class='green'>Reconnected to server</div>")
        else:
            self._disconnected_once = True
            self.reconnect()
            S("#global").append("<div class='red'>Disconnected from server</div>")

    def call(self, msg, callback):
        self._response_cb.append(callback)
        self.socket.emit("call", msg)

client = Client()