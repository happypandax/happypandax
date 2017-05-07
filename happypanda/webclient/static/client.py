__pragma__ ('alias', 'S', '$') # JQuery

class Base:
    
    def flash(self, msg, flash_type='normal'):
        """
        - normal
        - warning
        - critical
        """

        if flash_type == 'normal':
            S("#global").append("<div class='green'>{}</div>".format(msg))
        elif flash_type == 'warning':
            S("#global").append("<div class='orange'>{}</div>".format(msg))
        elif flash_type == 'critical':
            S("#global").append("<div class='red'>{}</div>".format(msg))

    def on_error(self, error, flash_type='critical'):
        if error:
            self.flash("{}: {}".format(error['code'], error['msg']), flash_type)

class Client(Base):

    def __init__(self):
        self.socket = io.connect()
        self.socket.on("connection", self.on_connect)
        self.socket.on("response", self.on_response)

        self.name = "webclient"
        self._disconnected_once = False
        self._connection_status = True
        self._response_cb = []
        self._last_msg = None

    def reconnect(self):
        def rc():
            if self._connection_status:
                clearInterval(con_interval)
                return
            self.socket.connect()
        con_interval = setInterval(rc, 5000)

    def on_response(self, msg):
        if self._response_cb:
            data = msg['data']
            if 'error' in data:
                self.on_error(data['error'])
            self._response_cb.pop(0)(msg)

    def on_connect(self, msg):
        self._connection_status = msg['status']
        con_text = "server connection: "
        text = "connected" if self._connection_status else "disconnected"
        con_text += text
        el = S("#serverstat")
        el.text(con_text)
        if self._connection_status:
            if self._disconnected_once:
                self.flash("Reconnected to server", 'normal')
        else:
            self._disconnected_once = True
            self.reconnect()
            self.flash("Disconnected from server", 'critical')

    __pragma__('kwargs')
    def call_function(self, func_name, callback, **kwargs):
        f_dict = {
            'fname': func_name
            }
        f_dict.update(kwargs)
        self.call([f_dict], callback)
    __pragma__('nokwargs')


    def call(self, msg, callback):
        self._response_cb.append(callback)

        final_msg = {
            'name': self.name,
            'data': msg
            }
        self._last_msg = final_msg
        self.socket.emit("call", final_msg)

client = Client()