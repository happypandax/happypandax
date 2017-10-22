from state import state
import utils

io = require('socket.io-client')

class ItemType:
    #: Gallery
    Gallery = 1
    #: Collection
    Collection = 2
    #: GalleryFilter
    GalleryFilter = 3
    #: Page
    Page = 4
    #: Gallery Namespace
    Grouping = 5
    #: Gallery Title
    Title = 6
    #: Gallery Artist
    Artist = 7
    #: Category
    Category = 8
    #: Language
    Language = 9
    #: Status
    Status = 10
    #: Circle
    Circle = 11
    #: GalleryURL
    GalleryUrl = 12
    #: Gallery Parody
    Parody = 13

class ImageSize:
    #: Original image size
    Original = 1
    #: Big image size
    Big = 2
    #: Medium image size
    Medium = 3
    #: Small image size
    Small = 4

class ViewType:
    #: Library
    Library = 1
    #: Favourite
    Favorite = 2
    #: Inbox
    Inbox = 3

class Base:

    def __init__(self, url=""):
        self._flashes = []

    def main(self):
        pass

    def log(self, msg):
        if state.debug:
            print(msg)

class ServerMsg:
    msg_id = 0

    __pragma__('kwargs')
    def __init__(self, data, callback=None, func_name=None, contextobj=None):
        ServerMsg.msg_id += 1
        self.id = self.msg_id
        self.data = data
        self.callback = callback
        self.func_name = func_name
        self.contextobj = contextobj
        self._msg = {}
    __pragma__('nokwargs')

    def call_callback(self, data, err):
        if self.contextobj:
            self.callback(self.contextobj, data, err)
        else:
            self.callback(data, err)



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
        self._reconnecting = False
        self._connection_status = True
        self._disconnected_once = False
        self._response_cb = {}
        self._first_connect = True
        self._last_msg = None
        self._cmd_status = {}
        self._cmd_status_c = 0
        self._retries = None
        self._poll_interval = 5
        self._poll_timeout = 1000*60*120
        self._last_retry = __new__(Date()).getTime()

        if not self.polling:
            self.socket.on("connect", self.on_connect)
            self.socket.on("disconnect", self.on_disconnect)
            utils.poll_func(self.connection, self._poll_timeout, self._poll_interval*1000)
            Client.polling = True
    __pragma__('nokwargs')

    def on_connect(self):
        self.call_func("get_config", self._set_debug, cfg={'core.debug':False})
        self.reconnect()

    def on_disconnect(self):
        self._connection_status = False
        self._disconnected_once = True
        state.app.notif("Disconnected from the server", "Server", "error")
        for x in state.commands:
            x.stop()

    def connection(self):
        self.send_command(self.commands['status'])
        if not self._connection_status and not self._reconnecting:
            self.log("Starting reconnection")
            utils.poll_func_stagger(self._reconnect, self._poll_timeout, self._poll_interval*1000)
            self._reconnecting = True
        return False

    __pragma__("tconv")
    def _reconnect(self):
        self.log("Reconnecting")
        last_interval = 100
        if self._retries is None:
            self._retries = list(range(10, last_interval+10, 10)) # secs
        i = self._retries.pop(0) if self._retries else last_interval
        if self._connection_status:
            i = 0
        else:
            self.reconnect(i)
        return i * 1000
    __pragma__("notconv")


    __pragma__("kwargs")
    def reconnect(self, interval = None):
        state.app.notif("Trying to establish server connection{}".format(
            ", trying again in {} seconds".format(interval) if interval else ""
            ), "Server")
        self.send_command(self.commands['connect'])
    __pragma__("nokwargs")

    def send_command(self, cmd):
        assert cmd in self.commands.values(), "Not a valid command"
        self.socket.emit("command", {'command': cmd})

    def on_command(self, msg):
        self._connection_status = msg['status']
        st_txt = "unknown"
        if self._connection_status:
            if self._disconnected_once or self._first_connect:
                self._disconnected_once = False
                self._first_connect = False
                state.app.notif("Connection to server has been established", "Server", 'success')
            st_txt = "connected"
            self._reconnecting = False
            self._retries = None
        else:
            self._disconnected_once = True
            st_txt = "disconnected"

    def on_error(self, msg):
        state.app.notif(msg['error'], "Server", "error")

    __pragma__('tconv')
    __pragma__('iconv')

    def on_server_call(self, msg):
        "Calls the designated callback."
        if self._response_cb:
            serv_msg = self._response_cb.pop(msg['id'])
            serv_data = msg['msg']
            if not serv_data:
                self.log("serv_data is null for message: {}".format(serv_msg._msg))
                self.log(msg)
            self.session = serv_data['session']
            if 'error' in serv_data:
                self.flash_error(serv_data['error'])
                if serv_data['error']['code'] == 408:
                    self.send_command(self.commands['handshake'])
            if serv_data['data'] == "Authenticated" and self._last_msg:
                    self.socket.emit("server_call", self._last_msg)
                    return
            if serv_msg.func_name and serv_data:
                for func in serv_data.data:
                    err = None
                    if 'error' in func:
                        err = func['error']
                        self.flash_error(err)
                    if func['fname'] == serv_msg.func_name:
                        if serv_msg.callback:
                            serv_msg.call_callback(func['data'], err)
                        break
            else:
                if serv_msg.callback:
                    serv_msg.call_callback(serv_data, None)
    __pragma__('noiconv')
    __pragma__('notconv')

    __pragma__('kwargs')

    def call_func(self, func_name, callback=None, ctx=None, **kwargs):
        "Call function on server. Calls callback with function data and error"
        f_dict = {
            'fname': func_name
        }
        f_dict.update(kwargs)
        return self.call(ServerMsg([f_dict], callback, func_name, ctx))
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
        servermsg._msg = final_msg
        return servermsg

    def flash_error(self, err):
        if err:
            state.app.notif(err['msg'], "Server({})".format(err['code']), "error")

    def _set_debug(self, data):
        state.debug = data['core.debug']

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
        self._stopped = False
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
    def stop(self, data=None, error=None):
        "Stop command"
        if data is not None and not error:
            states = []
            for i in self._command_ids:
                str_i = str(i)
                self._states[str_i] = data[str_i]
        elif error:
            pass
        else:
            self._stopped = True
            self.commandclient.call_func("stop_command", self.stop, command_ids=self._command_ids)
    __pragma__('noiconv')

    __pragma__('iconv')
    __pragma__('kwargs')
    def finished(self, any_command=False):
        "Check if command has finished running"
        if self._stopped:
            return True
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
                f = self.finished()
                if f:
                    state.commands.remove(self)
                return f

            state.commands.add(self)
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
            if self.finished(self._on_each) and not self._getting_value and not self._stopped:
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

