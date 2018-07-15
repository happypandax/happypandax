import uuid
import sys
import code
import arrow
import os
import gevent
import weakref
import gzip
import zlib
import errno

from inspect import getmembers, isfunction, signature, Parameter

from gevent import socket, pool
from gevent.server import StreamServer
from flask import Flask
from flask_socketio import SocketIO

from happypanda import interface
from happypanda.core.web import views
from happypanda.common import constants, exceptions, utils, hlogger, config
from happypanda.core import db, torrent, message, async_utils  # noqa: F401
from happypanda.interface import meta, enums
from happypanda.core.commands import meta_cmd

log = hlogger.Logger(constants.log_ns_server + __name__)


def list_api():
    "Returns {name : object}"
    _special_functions = tuple()  # functions we don't consider as part of the api
    all_functions = []
    mods = utils.get_package_modules(interface)
    for m in mods:
        all_functions.extend(getmembers(m, isfunction))
    funcs = {x[0]: x[1] for x in all_functions if not x[0]
             in _special_functions and not x[0].startswith('_')}
    log.d(f"Loaded {len(funcs)} Interface functions")
    return funcs


class Session:
    "Connection longevity"

    sessions = {}

    def __init__(self, id=None):
        self._id = id if id else uuid.uuid4().hex
        self.sessions[self._id] = self
        self._never_expire = not bool(config.session_span.value)
        self.extend()

    @property
    def id(self):
        return self._id

    @property
    def expired(self):
        if self._never_expire:
            return False
        return arrow.utcnow() > self._expiration

    def extend(self):
        "Extend the life of this session"
        if not self._never_expire:
            self._expiration = arrow.utcnow().replace(minutes=+config.session_span.value)

    @classmethod
    def get(cls, s_id):
        "Return a session object if it exists"
        return cls.sessions.get(s_id)


class ClientNotifications:
    _notifs = weakref.WeakValueDictionary()
    _actions = {}

    def __init__(self):
        pass

    def _context(self, ctx=None):
        if ctx is None:
            ctx = utils.get_context()
        if ctx is not None:
            notif_ctx = ctx.setdefault("notif", {})
            notif_ctx.setdefault("msg", [])
            notif_ctx.setdefault("rsp", [])
            return notif_ctx

    def push(self, msg, scope=None):
        """
        """
        assert isinstance(msg, message.Notification)
        ctx = self._context()
        self._notifs[msg.id] = msg
        cl = scope is None
        gl = scope is None

        if cl and ctx:
            ctx['msg'].insert(0, msg)

        if gl:
            log.d("Pushing notification on global scope")
            for wgl_ctx in ClientHandler.contexts.valuerefs():
                gl_ctx = wgl_ctx()
                if gl_ctx:
                    log.d("Pushing notification to context", gl_ctx['name'])
                    g_ctx = self._context(gl_ctx)
                    if cl and g_ctx == ctx:
                        continue
                    g_ctx['msg'].insert(0, msg)
        return self

    def reply(self, msg_id, action_values):
        """
        """
        v = {}
        for i, k in action_values.items():
            v[int(i)] = k
        self._actions[msg_id] = v

    def get(self, msg_id, timeout=constants.notif_normal_timeout):
        """
        """
        try:
            a = gevent.with_timeout(timeout, self._wait_action, msg_id)
        except gevent.Timeout:
            msg = self._notifs.get(msg_id, False)
            if msg:
                msg.expired = True
            a = None
        return a

    def _wait_action(self, msg_id):
        while True:
            try:
                return self._actions.pop(msg_id)
            except KeyError:
                pass
            utils.switch()

    def _pop(self, scope):
        try:
            ctx = self._context()
            if not ctx:
                log.d("Popping notification but no context found")
            else:
                log.d("Popping notification in context:", utils.get_context()['name'])
            r = ctx['msg'].pop() if ctx else None
        except IndexError:
            r = None
        return r

    def _fetch(self, scope=None, expired=True):
        ""
        while True:
            p = self._pop(scope)
            if p and p.expired and not expired:
                continue
            return p

    def __iter__(self):
        return self

    def __next__(self):
        return self._fetch()


class ClientContext(dict):
    pass


class ClientHandler:
    "Handles clients"

    api = list_api()

    contexts = weakref.WeakValueDictionary()  # session_id : context

    def __init__(self, client, address):
        self.errors = []
        self._client = client
        self._address = address
        self._ip = self._address[0]
        self._port = self._address[1]
        self._stopped = False
        self._accepted = False
        self.session = None
        self.context = utils.get_context(None).setdefault("ctx", ClientContext())
        self.handshake()

    def get_context(self, user=None, password=None):
        "Creates or retrieves existing context object for this client"
        s = constants.db_session()
        user_obj = None
        if user or password:
            log.d("Client provided credentials, authenticating...")
            if user == constants.super_user_name and not config.disable_default_user.value:
                log.d("Authenticating with default user")
                user_obj = s.query(
                    db.User).filter(
                    db.User.role == db.User.Role.default).one()
            else:
                user_obj = s.query(
                    db.User).filter(
                    db.User.name == user).one_or_none()
                if not user_obj or (not user_obj.role == db.User.Role.guest and not user_obj.password == password):
                    raise exceptions.AuthWrongCredentialsError(
                        utils.this_function(), "Wrong credentials")
        else:
            log.d("Client did not provide credentials")
            if not config.allow_guests.value:
                log.d("Guests are disallowed on this server")
                raise exceptions.AuthRequiredError(utils.this_function(), "Authentication is required")
            log.d("Authencticating as guest")
            user_obj = db.User(role=db.User.Role.guest)

        self.context['user'] = user_obj

        self.context['adresss'] = self._address
        if not self.context['user'].context_id:
            self.context['user'].context_id = uuid.uuid4().hex

        self.context['config'] = {}
        log.d("Client accepted")
        self._accepted = True

    @staticmethod
    def sendall(client, msg):
        """
        Send data to client
        Params:
            client --
            msg -- bytes
        """
        assert isinstance(msg, bytes)
        utils.switch(constants.Priority.High)
        msg = gzip.compress(msg, 5)
        log.d("Sending", sys.getsizeof(msg), "bytes to", client)
        client.sendall(msg)
        client.sendall(constants.postfix)

    def send(self, msg):
        """
        Wraps sendall
        """
        ClientHandler.sendall(self._client, msg)

    def parse(self, data):
        """
        Parse data from client
        Params:
            data -- data from client
        Returns:
            list of (function, function_kwargs)
        """
        where = "Message parsing"
        log.d("Parsing incoming data")
        try:
            j_data = utils.convert_to_json(data, where, log=log)

            log.d("Check if required root keys are present")
            # {"name":name, "data":data, 'session':id}
            root_keys = ('name', 'data', 'session')
            self._check_both(where, "JSON dict", root_keys, j_data)
        except exceptions.ServerError as e:
            raise

        self._check_session(j_data.get('session'))

        cmd = self._server_command(j_data)
        if cmd:
            return cmd

        if not self._accepted:
            self.handshake(j_data)
            return

        # 'data': [ list of function dicts ]
        function_keys = ('fname',)
        msg_data = j_data['data']
        if isinstance(msg_data, list):
            function_tuples = []
            for f in msg_data:
                try:
                    log.d("Cheking parameters in:", f)
                    self._check_missing(
                        where, "Function message", function_keys, f)
                except exceptions.InvalidMessage as e:
                    raise

                function_name = f['fname']
                try:
                    # check function
                    if function_name not in self.api:
                        e = exceptions.InvalidMessage(
                            where, "Function not found: '{}'".format(function_name))
                        self.errors.append((function_name, e))
                        continue

                    # check parameters
                    func_failed = False
                    func_args = tuple(
                        arg for arg in f if arg not in function_keys)
                    func_varnames = signature(self.api[function_name]).parameters
                    for arg in func_args:
                        if arg not in func_varnames:
                            e = exceptions.InvalidMessage(
                                where, "Unexpected argument in function '{}': '{}'".format(
                                    function_name, arg))
                            self.errors.append((function_name, e))
                            func_failed = True
                            break

                    for arg, def_val in func_varnames.items():
                        if def_val.default is Parameter.empty and arg not in func_args:
                            e = exceptions.InvalidMessage(
                                where, "Missing a required argument in function '{}': '{}'".format(
                                    function_name, arg))
                            self.errors.append((function_name, e))
                            func_failed = True

                    if func_failed:
                        continue

                    function_tuples.append(
                        (self.api[function_name], {x: f[x] for x in func_args}))
                except exceptions.ServerError as e:
                    self.errors.append((function_name, e))

            return function_tuples
        else:
            raise exceptions.InvalidMessage(
                where, "No list of function objects found in 'data'")

    def _check_both(self, where, msg, keys, data):
        "Invokes both missing and unknown key"
        self._check_missing(where, msg, keys, data)
        self._check_unknown(where, msg, keys, data)

    def _check_unknown(self, where, msg, keys, data):
        "Checks if there are unknown keys in provided data"
        if len(data) != len(keys):
            self._check_required_key(
                where, "{} contains unknown key '{}'".format(
                    msg, "{}"), keys, data)

    def _expect_iterable(self, where, data):
        if not isinstance(data, (list, dict, tuple)):
            raise exceptions.InvalidMessage(
                where, "A list/dict was expected, not: {}".format(data))

    def _check_missing(self, where, msg, keys, data):
        "Check if required keys are missing in provided data"
        self._check_required_key(
            where, "{} missing '{}' key".format(
                msg, "{}"), data, keys)

    def _check_required_key(self, where, msg, required_keys, data):
        ""
        for y in (required_keys, data):
            self._expect_iterable(where, y)
        for x in data:
            if x not in required_keys:
                raise exceptions.InvalidMessage(where, msg.format(x))

    def _check_session(self, session_id):
        "Authenticate client with session"
        log.d("Checking session id", session_id)
        if session_id:
            self.session = Session.get(session_id)
            if self.session:
                if self.session.expired:
                    raise exceptions.SessionExpiredError(utils.this_function(), self.session.id)

                if self.session.id in self.contexts:
                    self._accepted = True
                    self.context = self.contexts[self.session.id]
                    utils.get_context(None)['ctx'] = self.context
                    self.session.extend()
                    return

        log.d("Authentication with session failed", session_id)
        self._accepted = False

    def handshake(self, payload=None):
        """
        Sends a welcome message
        """
        assert payload is None or isinstance(payload, dict)
        if isinstance(payload, dict):
            log.d("Incoming handshake from client:", self._address)
            data = payload.get("data")
            if not config.allow_guests.value:
                log.d("Guests are not allowed, require keys")
                try:
                    self._check_both(
                        utils.this_function(), "JSON dict", ('user', 'password'), data)
                except exceptions.InvalidMessage as e:
                    raise exceptions.AuthMissingCredentials(utils.this_function(), e.msg)

            u = p = None

            if isinstance(data, dict):
                u = data.pop('user', None)
                p = data.pop('password', None)

            self.get_context(u, p)
            self.context['name'] = payload['name']
            self.session = Session()
            self.contexts[self.session.id] = self.context
            self.send(message.finalize("Authenticated", session_id=self.session.id))
        else:
            log.d("Sending handshake request to client:", self._address)
            msg = dict(
                version=meta.get_version().data(),
                guest_allowed=config.allow_guests.value,
            )

            self.send(message.finalize(msg))

    def advance(self, buffer):
        """
        Advance the loop for this client
        Params:
            buffer -- data buffer to be parsed
        """
        with db.cleanup_session():
            try:
                if constants.server_ready:
                    try:
                        buffer = gzip.decompress(buffer)
                    except (zlib.error, OSError) as e:
                        raise exceptions.ParsingError(utils.this_function(), str(e))

                    function_list = message.List("function", message.Function)
                    functions = self.parse(buffer)
                    if functions is None:
                        return
                    if isinstance(functions, enums.ServerCommand):
                        return functions

                    for func, func_args in functions:
                        log.d("Calling function", func, "with args", func_args)
                        func_msg = message.Function(func.__name__)
                        try:
                            msg = func(**func_args)
                            assert isinstance(msg, message.CoreMessage) or msg is None
                            func_msg.set_data(msg)
                        except exceptions.CoreError as e:
                            log.w(f"Error on func '{func.__name__}':", e)
                            func_msg.set_error(message.Error(e.code, e.msg))
                        function_list.append(func_msg)

                    # bad functions
                    for fname, e in self.errors:
                        function_list.append(
                            message.Function(
                                fname, error=message.Error(
                                    e.code, e.msg)))
                    self.errors.clear()

                    self.send(function_list.serialize(session_id=self.session.id))
                else:
                    self.on_wait()
            except exceptions.CoreError as e:
                log.w("Sending exception to client:", e)
                self.on_error(e)

            except Exception as e:
                if not constants.dev:
                    log.exception("An unhandled critical error has occurred")
                    if isinstance(e, (PermissionError, FileNotFoundError, NotImplementedError)):
                        self.on_error(exceptions.HappypandaError(str(e)))
                    else:
                        self.on_error(exceptions.HappypandaError(
                            f"An unhandled critical error has occurred: {e.__class__.__name__}"))
                else:
                    log.exception("An unhandled critical error has occurred")
                    raise

    def is_active(self):
        """
        Return bool indicating status of client
        """
        return not self._stopped

    def on_error(self, exception):
        """
        Creates and sends error message to client
        """
        assert isinstance(exception, exceptions.HappypandaError)
        e = message.Error(exception.code, exception.msg)
        s_id = self.session.id if self.session else ""
        self.send(message.finalize(None, error=e.json_friendly(False), session_id=s_id))

    def on_wait(self):
        """
        Sends wait message to client
        """
        s_id = self.session.id if self.session else ""
        self.send(message.Message("wait").serialize(session_id=s_id))

    def _server_command(self, data):
        d = data['data']
        if isinstance(d, (str, int)):
            try:
                e = enums.ServerCommand.get(d)
                if e in (enums.ServerCommand.ServerQuit, enums.ServerCommand.ServerRestart):
                    # TODO: check permission
                    pass
                return e
            except exceptions.EnumError:
                pass
        return None


class HPServer:
    "Happypanda Server"

    def __init__(self):
        params = utils.connection_params()
        self._pool = pool.Pool(
            config.allowed_clients.value if config.allowed_clients.value else None,
            async_utils.Greenlet)  # cannot be 0
        self._ssl_args = {}
        if config.enable_ssl.value is True or config.enable_ssl.value == "server":
            log.i("SSL enabled for server", stdout=True)
            self._ssl_args['ssl_context'] = utils.create_ssl_context(server_side=True)

        self._server = StreamServer(params,
                                    self._handle,
                                    spawn=self._pool,
                                    **self._ssl_args)
        self._clients = set()  # a set of client handlers
        self._exitcode = None

    def interactive(self):
        "Start an interactive session"
        api = locals().copy()
        api.pop("self")
        api.update(list_api())
        code.interact(
            banner="======== Start Happypanda Interactive ========",
            local=api)

    def _handle(self, client, address):
        "Client handle function"
        log.d("Client connected", str(address))
        handler = ClientHandler(client, address)
        self._clients.add(handler)
        try:
            buffer = b''
            while True:
                data, eof = utils.end_of_message(buffer)
                if eof:
                    buffer = data[1]
                    log.d("Received", sys.getsizeof(buffer), "bytes from ", address)
                    if handler.is_active():
                        client_msg = handler.advance(data[0])
                        if client_msg == enums.ServerCommand.RequestAuth:
                            handler.handshake()
                        elif client_msg == enums.ServerCommand.ServerQuit:
                            meta_cmd.ShutdownApplication().run()
                        elif client_msg == enums.ServerCommand.ServerRestart:
                            meta_cmd.RestartApplication().run()
                    else:
                        log.d("Client has disconnected", address)
                        break
                else:
                    log.d("Received data, EOF not reached. Waiting for more data from ", address)
                utils.switch(constants.Priority.High)
                r = client.recv(constants.data_size)
                if not r:
                    log.d("Client has disconnected", address)
                    break
                else:
                    buffer += r
        except ConnectionResetError:
            pass
        except socket.error as e:
            log.exception("Client disconnected with error", e)
        finally:
            self._clients.remove(handler)
        log.d("Client disconnected", str(address))

    def _start(self, blocking=True):
        try:
            constants.server_started = True
            meta_cmd.InitApplication().run()
            if blocking:
                log.i("Starting server... ({}:{})".format(
                    config.host.value, config.port.value), stdout=True)
                self._server.serve_forever()
            else:
                self._server.start()

        except OSError as e:
            if e.errno == errno.EADDRINUSE:
                log.w("Failed to start server because the address is already in use. Ensure that no other application or HPX isntances are using the same address")
            else:
                log.w("Failed to start server because of: {}".format(e.args[1]))

    def run(self, interactive=False):
        """Run the server
        Params:
            interactive -- Start in interactive mode (Note: Does not work with web server)
        """
        #tdaemon = torrent.start()
        try:
            self._start(not interactive)
            if interactive:
                self.interactive()
        except (KeyboardInterrupt, SystemExit):
            pass
        self._server.stop()
        # torrent.stop()
        # tdaemon.join()
        log.i("Server shutting down.", stdout=True)
        return self._exitcode

    def broadcast(self, msg):
        ""
        for c in self._clients.copy():
            c.send(message.finalize(msg, session_id=c.session.id if c.session else ""))

    def restart(self):
        self.broadcast(enums.ServerCommand.ServerRestart.value)
        if not self._exitcode:
            self._exitcode = constants.ExitCode.Restart
        self._cleanup()

    def shutdown(self):
        self.broadcast(enums.ServerCommand.ServerQuit.value)
        if not self._exitcode:
            self._exitcode = constants.ExitCode.Exit
        self._cleanup()

    def update(self, status=True, restart=True):
        if status and not (not constants.is_frozen and constants.dev):
            self._exitcode = constants.ExitCode.Update
            if restart:
                self.broadcast(enums.ServerCommand.ServerRestart.value)
                self._cleanup()

    def _cleanup(self):
        "note: this function never exits"
        if constants.web_proc:
            constants.web_proc.terminate()
        self._server.stop(10)


class WebServer:
    ""
    happyweb = Flask(__name__, static_url_path='/static',
                     template_folder=os.path.abspath(constants.dir_templates),
                     static_folder=os.path.abspath(constants.dir_static))
    happyweb.config['PROPAGATE_EXCEPTIONS'] = True  # enable only on debug?
    socketio = SocketIO(happyweb, async_mode="gevent")

    def run(self, host, port, dev=False, debug=False, logging_queue=None, cmd_args=None):
        if logging_queue:
            hlogger.Logger.setup_logger(cmd_args, logging_queue, dev=dev, debug=debug)
            utils.setup_online_reporter()
            utils.enable_loggers(config.enabled_loggers.value)

        if cmd_args is not None:
            utils.parse_options(cmd_args)
        views.init_views(self.happyweb, self.socketio)
        self._ssl_args = {}
        if config.enable_ssl.value is True or config.enable_ssl.value == "web":
            log.i("SSL enabled for webserver", stdout=True)
            self._ssl_args['ssl_context'] = utils.create_ssl_context(webserver=True, server_side=True)
            self._ssl_args['suppress_ragged_eofs'] = True
        try:
            self.socketio.run(self.happyweb, host, port, debug=False, **self._ssl_args)
        except KeyboardInterrupt:
            pass
