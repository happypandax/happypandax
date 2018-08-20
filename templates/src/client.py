from src.state import state
from src import utils
from org.transcrypt.stubs.browser import __pragma__, __new__

__pragma__('skip')
require = window = require = setInterval = setTimeout = setImmediate = None
clearImmediate = clearInterval = clearTimeout = this = document = None
JSON = Math = console = alert = requestAnimationFrame = None
js_undefined = location = locationStorage = sessionStorage = None
Date = None
__pragma__('noskip')

io = require('socket.io-client')


class TemporaryViewType:
    #: Contains gallery items to be added
    GalleryAddition = 1


class CommandState:

    #: command has not been put in any service yet
    out_of_service = 0

    #: command has been put in a service (but not started or stopped yet)
    in_service = 1

    #: command has been scheduled to start
    in_queue = 2

    #: command has been started
    started = 3

    #: command has finished succesfully
    finished = 4

    #: command has been forcefully stopped without finishing
    stopped = 5

    #: command has finished with an error
    failed = 6


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
    Url = 12
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
    #: A maximum width of 2400
    x2400 = 10
    #: A maximum width of 2400
    x1600 = 11
    #: A maximum width of 1280
    x1280 = 12
    #: A maximum width of 960
    x960 = 13
    #: A maximum width of 768
    x768 = 14


class ViewType:
    #: Contains all items except items in Trash
    All = 6
    #: Contains all items except items in Inbox and Trash
    Library = 1
    #: Contains all favourite items (mutually exclusive with items in Inbox)
    Favorite = 2
    #: Contains only items in Inbox
    Inbox = 3
    #: Contains only items in Trash
    Trash = 4
    #: Contains only items in ReadLater
    ReadLater = 5


class ItemSort:

    #: Gallery Random
    GalleryRandom = 1
    #: Gallery Title
    GalleryTitle = 2
    #: Gallery Artist Name
    GalleryArtist = 3
    #: Gallery Date Added
    GalleryDate = 4
    #: Gallery Date Published
    GalleryPublished = 5
    #: Gallery Last Read
    GalleryRead = 6
    #: Gallery Last Updated
    GalleryUpdated = 7
    #: Gallery Rating
    GalleryRating = 8
    #: Gallery Read Count
    GalleryReadCount = 9
    #: Gallery Page Count
    GalleryPageCount = 10

    #: Artist Name
    ArtistName = 20

    #: Namespace
    NamespaceTagNamespace = 30
    #: Tag
    NamespaceTagTag = 31

    #: Circle Name
    CircleName = 40

    #: Parody Name
    ParodyName = 45


class ProgressType:

    #: Unknown
    Unknown = 1
    #: Network request
    Request = 2
    #: A check for new update
    CheckUpdate = 3
    #: Updating application
    UpdateApplication = 4


class PluginState:

    #: Puporsely disabled
    Disabled = 0
    #: Unloaded because of dependencies, etc.
    Unloaded = 1
    #: Was just registered but not installed
    Registered = 2
    #: Allowed to be enabled
    Installed = 3
    #: Plugin is loaded and in use
    Enabled = 4
    #: Failed because of error
    Failed = 5


class PushID():
    Update = 1
    User = 200


def log(msg):
    print(msg)
    if state.debug:
        print(msg)


class Base:

    def __init__(self, url=""):
        self._flashes = []

    def main(self):
        pass

    def log(self, msg):
        log(msg)


class ServerMsg:
    msg_id = 0
    default_age = 1000 * 60 * 60
    server_results = utils.LRU({
        'max': 500,
        'maxAge': 1000 * 60 * 30,  # 30min
    })
    __pragma__('kwargs')

    def __init__(self, data, callback=None, func_name=None, contextobj=None,
                 memoize=False):
        ServerMsg.msg_id += 1
        self.id = self.msg_id
        self.data = data
        self.callback = callback
        self.func_name = func_name
        self.contextobj = contextobj
        self._msg = {}
        self.memoize = memoize * 1000 if isinstance(memoize, int) else memoize
        self._called = False
        if self.memoize:
            r = ServerMsg.server_results.js_get(utils.object_hash(self.data))
            if utils.defined(r):
                self.call_callback(r[0], r[1], skip_memoize=True)

    def call_callback(self, data, err, skip_memoize=False):
        if self.callback:
            if self.contextobj is not None:
                self.callback(self.contextobj, data, err)
            else:
                self.callback(data, err)
        if not skip_memoize and self.memoize:
            if not isinstance(self.memoize, int):
                self.memoize = ServerMsg.default_age
            ServerMsg.server_results.set(utils.object_hash(self.data), (data, err), self.memoize)
        self._called = True
    __pragma__('nokwargs')


class Client(Base):

    polling = False
    clients = []
    __pragma__('kwargs')

    def __init__(self, name="webclient", session="", namespace=""):
        self.clients.append(self)
        self.session_id = utils.storage.get("session_id")
        if not self.session_id:
            self.session_id = utils.random_string(10)
            utils.storage.set("session_id", self.session_id)
        self.socket_url = location.protocol + '//' + location.hostname + ':' + location.port + namespace
        self.socket = io(self.socket_url, {'transports': ['websocket']})
        self.socket.on("command", self.on_command)
        self.socket.on("server_call", self.on_server_call)
        self.socket.on("exception", self.on_error)
        self.socket.on("connect", self.on_connect)
        self.socket.on("disconnect", self.on_disconnect)

        self.commands = {
            'connect': 1,
            'reconnect': 2,
            'disconnect': 3,
            'status': 4,
            'handshake': 5,
            'rehandshake': 6
        }
        self.command_callbacks = {}

        self.namespace = namespace
        self.session = session
        self.name = name
        self._reconnecting = False
        self._connection_status = True
        self._disconnected_once = False
        self._initial_socket_connection = False
        self._socket_connection = False
        self._response_cb = {}
        self._first_connect = True
        self._msg_queue = []
        self._last_msg = None
        self._cmd_status = {}
        self._cmd_status_c = 0
        self._retries = None
        self._poll_interval = 5
        self._poll_timeout = 1000 * 60 * 120
        self._last_retry = __new__(Date()).getTime()
        self._prev_retry_interval = 0

        self.polling = False
        if not Client.polling:
            utils.poll_func(self.connection, self._poll_timeout, self._poll_interval * 1000)
            self.polling = True
            Client.polling = True
    __pragma__('nokwargs')

    def on_connect(self):
        self._socket_connection = True
        self._initial_socket_connection = True
        if self.polling:
            self.reconnect()

        if len(self._msg_queue):
            while len(self._msg_queue):
                self.socket.emit("server_call", self._msg_queue.pop(0))

    def on_disconnect(self):
        state['connected'] = False
        self.session = ""
        self._socket_connection = False
        self._connection_status = False
        self._disconnected_once = True
        if self.polling:
            if state.app:
                state.app.notif("Disconnected from the server", "Server", "error")
        for x in state.commands:
            x.stop()

    def connection(self):
        self.send_command(self.commands['status'])
        if not self._connection_status and not self._reconnecting:
            self.log("Starting reconnection")
            utils.poll_func_stagger(self._reconnect, self._poll_timeout, self._poll_interval * 1000)
            self._reconnecting = True
        return False

    __pragma__("tconv")

    def _reconnect(self):
        if state['active']:
            self.log("Reconnecting")
            last_interval = 100
            if self._retries is None:
                self._retries = list(range(10, last_interval + 10, 10))  # secs
            self._prev_retry_interval = self._retries.pop(0) if self._retries else last_interval
            if self._connection_status:
                self._prev_retry_interval = 0
            else:
                self.reconnect(self._prev_retry_interval)
        else:
            if not self._prev_retry_interval:
                self._prev_retry_interval = 5
        return self._prev_retry_interval * 1000
    __pragma__("notconv")

    __pragma__("kwargs")

    def reconnect(self, interval=None):
        if not state['active']:
            return
        if state.app:
            state.app.notif("Trying to establish server connection{}".format(
                ", trying again in {} seconds".format(interval) if interval else ""
            ), "Server")
        self.send_command(self.commands['connect'])

    def send_command(self, cmd, extra=None, callback=None):
        if cmd not in self.commands.values():
            self.log("Not a valid command")
            return
        ServerMsg.msg_id += 1
        msg = {'id': ServerMsg.msg_id, 'command': cmd, 'session_id': self.session_id}
        if extra:
            msg.update(extra)
        if callback:
            self.command_callbacks[msg['id']] = callback
        self.socket.emit("command", msg)
    __pragma__("nokwargs")

    __pragma__('iconv')

    def on_command(self, msg):
        for c in self.clients:
            c._connection_status = msg['status']
        state['connected'] = self._connection_status
        state['accepted'] = msg['accepted']
        state['guest_allowed'] = msg['guest_allowed']
        state['version'] = msg['version']

        if msg['command'] in (self.commands['handshake'], self.commands['rehandshake'])\
           or self._connection_status and self._first_connect:
            if msg['accepted']:
                self.call_func("get_config", self._set_debug, cfg={'core.debug': False})
                self.call_func("get_locales", self._set_locales)
                self.call_func("check_update", push=True)
                self.get_translations()
        else:
            if state['app']:
                state['app'].on_login(state['accepted'])

        if self._connection_status:
            if msg['command'] in (self.commands['connect'], self.commands['reconnect']):
                if not utils.session_storage.get("startup_update", False):
                    utils.session_storage.set("startup_update", True)
            if self._disconnected_once or self._first_connect:
                self._disconnected_once = False
                self._first_connect = False
                if state.app:
                    state.app.notif("Connection to server has been established", "Server", 'success')
            self._reconnecting = False
            self._retries = None
        else:
            self._disconnected_once = True

        if msg['id'] in self.command_callbacks:
            cmd_cb = self.command_callbacks.pop(msg['id'])
            if cmd_cb:
                cmd_cb(msg)

    __pragma__('noiconv')

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
                return
            self.session = serv_data['session']
            if 'error' in serv_data:
                self.flash_error(serv_data['error'])
                if serv_data['error']['code'] == 408:
                    self.send_command(self.commands['rehandshake'])
            if serv_data['data'] == "Authenticated":
                serv_msg = self._response_cb[serv_msg.id] = serv_msg
                self.socket.emit("server_call", serv_msg._msg)
                return
            if serv_msg.func_name and serv_data:
                if serv_data.data != None:  # noqa: E711
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
                        err = None
                        if serv_data['error']:
                            err = serv_data['error']
                        serv_msg.call_callback(None, err)
            else:
                if serv_msg.callback:
                    serv_msg.call_callback(serv_data, None)
    __pragma__('noiconv')
    __pragma__('notconv')

    __pragma__('kwargs')

    def call_func(self, func_name, callback=None, ctx=None, _memoize=False, **kwargs):
        "Call function on server. Calls callback with function data and error"
        f_dict = {
            'fname': func_name
        }
        f_dict.update(kwargs)
        return self.call(ServerMsg([f_dict], callback, func_name, ctx, memoize=_memoize))
    __pragma__('nokwargs')

    def call(self, servermsg):
        "Send data to server. Calls callback with received data."
        assert isinstance(servermsg, ServerMsg)
        if servermsg._called:
            return servermsg
        self._response_cb[servermsg.id] = servermsg
        final_msg = {
            'session_id': self.session_id,
            'id': servermsg.id,
            'msg': {
                'session': self.session,
                'name': self.name,
                'data': servermsg.data
            }
        }

        self._last_msg = final_msg
        if self._connection_status and self._socket_connection and state['accepted']:
            self.socket.emit("server_call", final_msg)
        else:
            if not self._initial_socket_connection:
                self._msg_queue.append(final_msg)
        servermsg._msg = final_msg
        return servermsg

    def flash_error(self, err):
        if err:
            state.app.notif(err['msg'], "Server({})".format(err['code']), "error")

    def set_locale(self, l):
        a, b = l.split('_')
        l = "{}-{}".format(a, b.upper())
        utils.moment.locale(l)

    __pragma__("kwargs")

    def get_translations(self, data=None, error=None, locale=None):
        if data is not None and not error:
            state['translations'] = data
        else:
            self.call_func("get_translations", self.get_translations, locale=locale)
    __pragma__("nokwargs")

    def _set_debug(self, data):
        state.debug = data['core.debug']
        if state.app:
            state.app.setState({'debug': state.debug})
        if state.debug:
            state.translation_id_error = utils.storage.get("translation_id_error", False)
            state.untranslated_text = utils.storage.get("untranslated_text", True)

    def _set_locales(self, data):
        state.locales = data
        l = utils.storage.get("locale", False)
        if l:
            self.set_locale(l)
            self.call_func("set_config", None, cfg={'client.translation_locale': l})


client = Client()
pushclient = Client("push", namespace="/notification")
commandclient = Client("command", namespace="/command")


class Command(Base):
    __pragma__("kwargs")

    def __init__(self, command_ids, customclient=None, daemon=True):
        super().__init__()
        assert command_ids is not None
        self.daemon = daemon
        self._single_id = None
        if isinstance(command_ids, int):
            self._single_id = command_ids
            command_ids = [command_ids]

        self._command_ids = command_ids
        self._states = {}
        self._progress = {}
        self._values = {}
        self._value_callback = None
        self._getting_value = False
        self._stopped = False
        self._on_each = False
        self._complete_callback = None
        self._progress_callback = None
        self._error = False
        self.commandclient = commandclient

        for i in self._command_ids:
            self._states[str(i)] = None

        if customclient:
            self.commandclient = customclient
    __pragma__("nokwargs")

    __pragma__('iconv')

    def _check_status(self, data=None, error=None):
        if data is not None and not error:
            for i in self._command_ids:
                str_i = str(i)
                self._states[str_i] = data[str_i]
        elif error:
            self._error = True
        else:
            self.commandclient.call_func("get_command_state", self._check_status, command_ids=self._command_ids)
    __pragma__('noiconv')

    __pragma__('iconv')

    def stop(self, data=None, error=None):
        "Stop command"
        if data is not None and not error:
            for i in self._command_ids:
                str_i = str(i)
                self._states[str_i] = data[str_i]
        elif error:
            if "does not exist" in error['msg']:
                for i in self._command_ids:
                    str_i = str(i)
                    self._states[str_i] = CommandState.stopped
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

    def poll_until_complete(self, interval=1000 * 5, timeout=1000 * 60 * 120, callback=None):
        "Keep polling for command state until it has finished running"
        self._complete_callback = callback
        if not self.finished():

            def _poll():
                if state.connected and not self._error:
                    self._fetch_value()
                    if not self.finished():
                        self._check_status()
                    else:
                        if self._complete_callback:
                            self._complete_callback(self)

                    f = self.finished()
                    if f:
                        state.commands.remove(self)
                    return f
                return False

            state.commands.add(self)
            utils.poll_func(_poll, timeout, interval)
        else:
            self._fetch_value()
            if self._complete_callback:
                self._complete_callback(self)
    __pragma__('nokwargs')

    __pragma__('iconv')

    def _fetch_progress(self, data=None, error=None):
        "Stop command"
        if data is not None and not error:
            for i in self._command_ids:
                str_i = str(i)
                self._progress[str_i] = data[str_i]
        elif error:
            self._error = True
        else:
            self.commandclient.call_func("get_command_progress", self._fetch_progress, command_ids=self._command_ids)
    __pragma__('noiconv')

    __pragma__('kwargs')

    def poll_progress(self, interval=1000 * 3, timeout=1000 * 60 * 120, callback=None):
        "Keep polling for command progress until it has finished running"
        self._progress_callback = callback
        if not self.finished():

            def _poll():
                if state.connected and not self._error:
                    if not self.finished():
                        self._check_status()
                    self._fetch_progress()
                    if self._progress_callback:
                        self._progress_callback(self)
                    f = self.finished()
                    return f
                return False

            utils.poll_func(_poll, timeout, interval)
        else:
            self._fetch_progress()
            if self._progress_callback:
                self._progress_callback(self)
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
            self._error = True
        else:
            if self.finished(self._on_each) and not self._getting_value and not self._stopped:
                if not cmd_ids:
                    cmd_ids = []
                    for i in self._command_ids:
                        str_i = str(i)
                        if str_i not in self._values and str_i in self._states:
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
    __pragma__('kwargs')

    def get_value(self, cmd_id=None, block=False):
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

        if block and not self.finished():
            self.poll_until_complete(3000)
            while True:
                if self.finished():
                    break

        if self._single_id:
            return self._values[str(self._single_id)]
        return self._values

    __pragma__('nokwargs')
    __pragma__('noiconv')
    __pragma__('notconv')

    def get_progress(self, cmd_id=None):
        "Fetch command progress"

        if cmd_id and not isinstance(cmd_id, list):
            cmd_id = [str(cmd_id)]

        if not cmd_id:
            cmd_id = self._command_ids

        ids = []
        for i in cmd_id:
            if i not in self._progress:
                ids.append(int(i))

        if ids:
            self._fetch_progress()

        if self._single_id:
            return self._progress[str(self._single_id)]
        return self._progress

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
