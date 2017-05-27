__pragma__('alias', 'S', '$')  # JQuery


class URLManipulator:

    def go(self, url):
        "Add state to History"
        history.pushState(null, null, url)


class Base:

    def __init__(self, url=""):
        self.url = url
        self.url_manipulator = URLManipulator()

    def main(self):
        raise NotImplementedError

    def flash(self, msg, flash_type='danger', strong=""):
        """
        - info
        - sucess
        - warning
        - danger
        """

        lbl = 'alert-' + flash_type
        self.compile(
            "#global-flash-t",
            "#global-flash",
            append=True,
            alert=lbl,
            strong=strong,
            msg=msg)

    def get_label(self, label_type):
        """
        - default
        - primary
        - success
        - info
        - warning
        - danger
        """
        return 'label-' + label_type

    __pragma__('kwargs')

    def compile(
            self,
            source_el,
            target_el,
            after=None,
            before=None,
            append=None,
            prepend=None,
            **data):
        """
        Compile template element
        Set after, before, append or prepend to True to specify where to insert html.
        """

        tmpl = Handlebars.compile(S(source_el).html())
        if after:
            S(target_el).after(tmpl(data)).fadeIn()
        elif before:
            S(target_el).before(tmpl(data)).fadeIn()
        elif append:
            S(target_el).append(tmpl(data)).fadeIn()
        elif prepend:
            S(target_el).prepend(tmpl(data)).fadeIn()
        else:
            S(target_el).html(tmpl(data)).fadeIn()
    __pragma__('nokwargs')

    def on_error(self, error, flash_type='danger'):
        if error:
            self.flash(error['msg'], flash_type, error['code'])


class Client(Base):

    def __init__(self):
        self.socket = io.connect()
        self.socket.on("serv_connect", self.on_connect)
        self.socket.on("response", self.on_response)

        self.name = "webclient"
        self._disconnected_once = False
        self._connection_status = True
        self._response_cb = []
        self._last_msg = None

    def reconnect(self):
        con_interval = None

        def rc():
            if self._connection_status:
                clearInterval(con_interval)
                return
            self.socket.emit("reconnect", {})
        con_interval = setInterval(rc, 5000)

    def on_response(self, msg):
        "Calls the designated callback."
        if self._response_cb:
            if 'error' in msg:
                self.on_error(msg['error'])
            cb = self._response_cb.pop(0)
            if isinstance(cb, tuple):  # TODO: consider revising lol
                func_name, cb = cb
                for func in msg['data']:
                    err = None
                    if 'error' in func:
                        self.on_error(func['error'])
                        err = func['error']
                    if func['fname'] == func_name:
                        cb(func['data'], err)
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
                self.flash("Reconnected to server", 'success')
        else:
            st_txt = "disconnected"
            st_label = self.get_label("danger")
            self._disconnected_once = True
            self.reconnect()
            self.flash("Disconnected from server", 'warning')

        self.compile("#server-status-t", "#server-status", **
                     {"status": st_txt, "label": st_label})
    __pragma__('kwargs')

    def call_func(self, func_name, callback, **kwargs):
        "Call function on server. Calls callback with function data and error"
        f_dict = {
            'fname': func_name
        }
        f_dict.update(kwargs)
        self.call([f_dict], (func_name, callback))
    __pragma__('nokwargs')

    def call(self, data, callback):
        "Send data to server. Calls callback with received data."
        if self._connection_status:
            self._response_cb.append(callback)

            final_msg = {
                'name': self.name,
                'data': data
            }
            self._last_msg = final_msg
            self.socket.emit("call", final_msg)


client = Client()
