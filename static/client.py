__pragma__('alias', 'S', '$')  # JQuery

import utils

debug = True


class Base:

    def __init__(self, url=""):
        self.url = utils.URLManipulator(url)
        self._flashes = []

    def main(self):

        if self.url:

            self.log("setting active menu item")

            def each_d(index):

                aurl = S(this).find('a').attr("href")
                if aurl == self.url.path():
                    S(this).addClass("active")
                    S(this).find('a').append('<span class="sr-only">(current)</span>')

            S("#nav-collapse li").each(each_d)

    def log(self, msg):
        if debug:
            print(msg)

    def flash(self, msg, flash_type='danger', strong=""):
        """
        - info
        - sucess
        - warning
        - danger
        """

        lbl = 'alert-' + flash_type
        obj = self.compile(
            "#global-flash-t",
            "#global-flash",
            prepend=True,
            alert=lbl,
            strong=strong,
            msg=msg)
        obj.delay(8000).fadeOut(500)

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

        Returns inserted element
        """
        src = S(source_el).html()
        if not src:
            console.error("{} could not be found, compilation aborted".format(source_el))
            return
        tmpl = Handlebars.compile(src)
        if after:
            return S(tmpl(data)).insertAfter(target_el)
        elif before:
            return S(tmpl(data)).insertBefore(target_el)
        elif append:
            return S(tmpl(data)).appendTo(target_el)
        elif prepend:
            return S(tmpl(data)).prependTo(target_el)
        else:
            return S(target_el).html(tmpl(data))
    __pragma__('nokwargs')

    def flash_error(self, error, flash_type='danger'):
        if error:
            self.flash(error['msg'], flash_type, error['code'])


class ServerMsg:
    msg_id = 0

    def __init__(self, data, callback=None, func_name=None):
        ServerMsg.msg_id += 1
        self.id = self.msg_id
        self.data = data
        self.callback = callback
        self.func_name = func_name


class Client(Base):

    polling = False

    __pragma__('kwargs')
    def __init__(self, session="", namespace=""):
        self.socket_url = location.protocol+'//'+location.hostname+':'+location.port+namespace
        self.socket = io(self.socket_url, {'transports': ['websocket']})
        self.socket.on("command", self.on_command)
        self.socket.on("server_call", self.on_server_call)
        self.socket.on("exception", self.on_error)

        self.commands = {
            'connect': 1,
            'reconnect': 2,
            'disconnect': 3,
            'status': 4,
            'handshake': 5
        }

        self.namespace = namespace
        self.session = session
        self.name = "webclient"
        self._connection_status = True
        self._disconnected_once = False
        self._response_cb = {}
        self._last_msg = None
        self._msg_queue = []
        self._cmd_status = {}
        self._cmd_status_c = 0

        if not self.polling:
            utils.poll_func(self.connection, 3000000, 15000)
            Client.polling = True
    __pragma__('nokwargs')

    def connection(self):
        self.send_command(self.commands['status'])
        if not self._connection_status:
            self.flash("Trying to establish server connection...", 'info')
            self.send_command(self.commands['connect'])
        return False

    def send_command(self, cmd):
        assert cmd in self.commands.values(), "Not a valid command"
        self.socket.emit("command", {'command': cmd})

    def on_command(self, msg):

        self._connection_status = msg['status']
        st_txt = "unknown"
        st_label = self.get_label("default")
        if self._connection_status:
            if self._disconnected_once:
                self._disconnected_once = False
                self.flash("Connection to server has been established", 'success')
            st_txt = "connected"
            st_label = self.get_label("success")
        else:
            self._disconnected_once = True
            st_txt = "disconnected"
            st_label = self.get_label("danger")

        self.compile("#server-status-t", "#server-status", **
                     {"status": st_txt, "label": st_label})

    def on_error(self, msg):
        self.flash(msg['error'], 'danger')

    __pragma__('tconv')
    __pragma__('iconv')

    def on_server_call(self, msg):
        "Calls the designated callback."
        if self._response_cb:
            serv_msg = self._response_cb.pop(msg['id'])
            serv_data = msg['msg']
            self.session = serv_data['session']
            if 'error' in serv_data:
                self.flash_error(serv_data['error'])
                if serv_data['error']['code'] == 408:
                    self.send_command(self.commands['handshake'])
            if serv_msg.func_name and serv_data:
                for func in serv_data.data:
                    err = None
                    if 'error' in func:
                        err = func['error']
                        self.flash_error(err)
                    if func['fname'] == serv_msg.func_name:
                        if serv_msg.callback:
                            serv_msg.callback(func['data'], err)
                        break
            else:
                if serv_msg.callback:
                    serv_msg.callback(serv_data)
    __pragma__('noiconv')
    __pragma__('notconv')

    __pragma__('kwargs')

    def call_func(self, func_name, callback, **kwargs):
        "Call function on server. Calls callback with function data and error"
        f_dict = {
            'fname': func_name
        }
        f_dict.update(kwargs)
        self.call(ServerMsg([f_dict], callback, func_name))
    __pragma__('nokwargs')

    def call(self, servermsg):
        "Send data to server. Calls callback with received data."
        assert isinstance(servermsg, ServerMsg)
        self._response_cb[servermsg.id] = servermsg
        final_msg = {
            'id': servermsg.id,
            'msg': {
                'session': self.session,
                'name': self.name,
                'data': servermsg.data
            }
        }

        self._last_msg = final_msg
        if self._connection_status:
            self.socket.emit("server_call", final_msg)
        else:
            self._msg_queue.append(final_msg)

client = Client()
thumbclient = Client(namespace="/thumb")
commandclient = Client(namespace="/command")

class Command(Base):

    def __init__(self, command_ids, customclient=None):
        super().__init__()
        assert command_ids is not None
        self._single_id = None
        if isinstance(command_ids, int):
            self._single_id = command_ids
            command_ids = [command_ids]

        self._command_ids = command_ids
        self._states = {}
        self._values = {}
        self._value_callback = None
        self._getting_value = False
        self._on_each = False
        self._complete_callback = None
        self.commandclient = commandclient

        for i in self._command_ids:
            self._states[str(i)] = None

        if customclient:
            self.commandclient = customclient

    __pragma__('iconv')

    def _check_status(self, data=None, error=None):
        if data is not None and not error:
            states = []
            for i in self._command_ids:
                str_i = str(i)
                self._states[str_i] = data[str_i]
        elif error:
            pass
        else:
            self.commandclient.call_func("get_command_state", self._check_status, command_ids=self._command_ids)
    __pragma__('noiconv')

    __pragma__('iconv')

    __pragma__('kwargs')
    def finished(self, any_command=False):
        "Check if command has finished running"
        states = []
        for s in self._states:
            states.append(self._states[s] in ['finished', 'stopped', 'failed'])
        if any_command:
            t = any(states)
        else:
            t = all(states)
        return t
    __pragma__('nokwargs')
    __pragma__('noiconv')

    __pragma__('kwargs')
    def poll_until_complete(self, interval=1000 * 5, timeout=1000 * 60 * 10, callback=None):
        "Keep polling for command state until it has finished running"
        self._complete_callback = callback
        if not self.finished():

            def _poll():
                if not self.finished():
                    self._check_status()
                else:
                    if self._complete_callback:
                        self._complete_callback()

                self._fetch_value()
                return self.finished()

            utils.poll_func(_poll, timeout, interval)
        else:
            if self._complete_callback:
                self._complete_callback()
    __pragma__('nokwargs')

    __pragma__('iconv')
    __pragma__('kwargs')

    def _fetch_value(self, data=None, error=None, cmd_ids=None):
        if data is not None and not error:

            for i in self._command_ids:
                str_i = str(i)
                if str_i in data:
                    self._values[str_i] = data[str_i]

                    if self._on_each and self._value_callback:
                        self._value_callback(i, self._values[str_i])

            if not self._on_each and self._value_callback:
                self._value_callback(self)

            self._getting_value = False
        elif error:
            pass
        else:
            if self.finished(self._on_each) and not self._getting_value:
                if not cmd_ids:
                    cmd_ids = []
                    for i in self._command_ids:
                        str_i = str(i)
                        if not str_i in self._values and str_i in self._states:
                            if self._states[str_i] == 'finished':
                                cmd_ids.append(i)
                            if self._on_each and self._value_callback:
                                if self._states[str_i] in ['stopped', 'failed']:
                                    self._value_callback(i, None)

                self.commandclient.call_func("get_command_value", self._fetch_value, command_ids=cmd_ids)
                self._getting_value = True
    __pragma__('nokwargs')
    __pragma__('noiconv')

    __pragma__('iconv')
    __pragma__('tconv')

    def get_value(self, cmd_id=None):
        "Fetch command value"

        if cmd_id and not isinstance(cmd_id, list):
            cmd_id = [str(cmd_id)]

        if not cmd_id:
            cmd_id = self._command_ids

        ids = []
        for i in cmd_id:
            if i not in self._values:
                ids.append(int(i))

        if ids:
            self._fetch_value(cmd_ids=ids)

        if self._single_id:
            return self._values[str(self._single_id)]
        return self._values
    __pragma__('noiconv')
    __pragma__('notconv')

    __pragma__('kwargs')
    def set_callback(self, callback, on_each_complete=False):
        """
        Set a callback for when the value has been obtained
        The callback is called with this command

        on_each_complete: call callback with command_id and value on each complete state
        """
        self._value_callback = callback
        self._on_each = on_each_complete
    __pragma__('nokwargs')

    def done(self):
        "all values has been fetched"
        return len(self._values.keys()) == len(self._states.keys())
