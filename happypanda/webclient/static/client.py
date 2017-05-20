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

    def get_label(self, label_type):
        """
        - default
        - primary
        - success
        - info
        - warning
        - danger
        """
        return 'label-'+label_type

    def compile(self, source_el, target_el, data):
        """
        Compile template element
        """
        
        if not source_el.startswith(('.', '#')):
            source_el= '#'+source_el
        if not target_el.startswith(('.', '#')):
            target_el= '#'+target_el

        tmpl = Handlebars.compile(S(source_el).html())
        S(target_el).html(tmpl(data))


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
            if 'error' in msg:
                self.on_error(msg['error'])
            cb = self._response_cb.pop(0)
            if isinstance(cb, tuple): # TODO: consider revising lol
                func_name, cb = cb
                for func in msg['data']:
                    if 'error' in func:
                        self.on_error(func['error'])
                    if func['fname'] == func_name:
                        cb(func['data'])
                        break
            else:
                cb(msg)

    def on_connect(self, msg):
        self._connection_status = msg['status']
        st_txt = "unknown"
        st_label = self.get_label("default")
        if self._connection_status:
            st_txt = "connected"
            st_label = self.get_label("success")
            if self._disconnected_once:
                self.flash("Reconnected to server", 'normal')
        else:
            st_txt = "disconnected"
            st_label = self.get_label("danger")
            self._disconnected_once = True
            self.reconnect()
            self.flash("Disconnected from server", 'critical')

        self.compile("server-status-t", "server-status", {"status": st_txt,
                                                           "label": st_label})

    __pragma__('kwargs')
    def call_func(self, func_name, callback, **kwargs):
        f_dict = {
            'fname': func_name
            }
        print(kwargs)
        f_dict.update(kwargs)
        self.call([f_dict], (func_name, callback))
    __pragma__('nokwargs')


    def call(self, data, callback):
        self._response_cb.append(callback)

        final_msg = {
            'name': self.name,
            'data': data
            }
        self._last_msg = final_msg
        self.socket.emit("call", final_msg)

client = Client()