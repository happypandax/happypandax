import enum
import arrow
import gevent

from contextlib import contextmanager
from abc import ABCMeta, abstractmethod
from inspect import isclass
from gevent.threadpool import ThreadPool

from happypanda.common import utils, hlogger, exceptions, constants
from happypanda.core import plugins

log = hlogger.Logger(__name__)


def get_available_commands():
    subs = utils.all_subclasses(Command)
    commands = set()
    for c in subs:
        c._get_commands()
        for a in c._entries:
            commands.add(c.__name__ + '.' + c._entries[a].name)
    return commands


class CommandState(enum.Enum):

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


class CommandFuture:

    class NoValue:
        pass

    def __init__(self, cmd, f):
        self._cmd = cmd
        self._future = f
        self._value = self.NoValue

    def get(self, block=True, timeout=None):
        if not self._value == self.NoValue:
            return self._value
        if block:
            gevent.wait([self._future], timeout)
            self._value = self._future.get()
        else:
            self._value = self._future.get(block, timeout)
        return self._value

    def kill(self):
        self._future.kill()


def _daemon_greenlet():
    while True:
        utils.switch(constants.Priority.Low)


def _native_runner(f):

    def cleanup_wrapper(*args, **kwargs):
        r = f(*args, **kwargs)
        constants._db_scoped_session.remove()
        return r

    def wrapper(*args, **kwargs):
        # d = gevent.spawn(_daemon_greenlet)  # this is to allow gevent switching to occur
        #g = gevent.spawn(cleanup_wrapper, *args, **kwargs)
        #r = g.get()
        # d.kill()
        return cleanup_wrapper(*args, **kwargs)
    return wrapper


class CoreCommand():
    "Base command"

    _events = {}
    _entries = {}
    _native_pool = None

    def __new__(cls, *args, **kwargs):
        obj = super(CoreCommand, cls).__new__(cls)
        obj._get_commands()
        return obj

    def __init__(self, priority=constants.Priority.Normal):
        self._created_time = arrow.now()
        self.command_id = None
        self._started_time = None
        self._finished_time = None
        self._priority = priority
        self._futures = []

    def run_native(self, f, *args, **kwargs):
        f = CommandFuture(self, self._native_pool.apply_async(_native_runner(f), args, kwargs))
        self._futures.append(f)
        return f

    def kill(self):
        [f.kill() for f in self._futures]

    def _log_stats(self, d=None):
        create_delta = self._finished_time - self._created_time
        run_delta = self._finished_time - self._started_time
        log_delta = (d - self._finished_time) if d else None
        log.i("Command - '{}' -".format(self.__class__.__name__), "ID({})".format(self.command_id) if self.command_id else '',
              "running time:\n",
              "\t\tCreation delta: {} (time between creation and finish)\n".format(create_delta),
              "\t\tRunning delta: {} (time between start and finish)\n".format(run_delta),
              "\t\tLog delta: {} (time between finish and this log)\n".format(log_delta),
              )

    @classmethod
    def _get_commands(cls):
        ""
        for a in cls.__dict__.values():
            if isinstance(a, CommandEvent):
                a.command_cls = cls
                cls._events[a.name] = a

            if isinstance(a, CommandEntry):
                a.command_cls = cls
                cls._entries[a.name] = a


class Command(CoreCommand, metaclass=ABCMeta):

    def __init__(self, priority=constants.Priority.Normal):
        super().__init__(priority)
        self._main = self.main
        self.main = self._main_wrap

    def run(self, *args, **kwargs):
        """
        Run the command with *args and **kwargs.
        """
        log.d("Running command:", self.__class__.__name__)
        return self.main(*args, **kwargs)

    def _main(self):
        pass

    def _main_wrap(self, *args, **kwargs):
        utils.switch(self._priority)
        self._started_time = arrow.now()
        r = self._main(*args, **kwargs)
        self._finished_time = arrow.now()
        return r

    @abstractmethod
    def main(self, *args, **kwargs):
        pass


class UndoCommand(Command):
    "Command capable of undoing itself"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @abstractmethod
    def undo(self):
        pass


class AsyncCommand(Command):
    "Async command"

    def __init__(self, service=None, priority=constants.Priority.Normal):
        super().__init__(priority)

        self._service = service
        self._args = None
        self._kwargs = None
        self.state = CommandState.out_of_service
        self.exception = None

        if self._service:
            service.add_command(self)

    @property
    def value(self):
        self._ensure_service()
        return self._service.get_command_value(self.command_id)

    @property
    def service(self):
        "Returns the service that manages this command"
        return self._service

    @service.setter
    def service(self, s):
        # TODO: remove from other services

        self._service = s

    def _ensure_service(self):
        if not self._service:
            n = self.__class__.__name__
            raise exceptions.CommandError(
                n, "Command '{}' has not been added to any service".format(n))

    def stop(self):
        "Stop running this command"
        self._ensure_service()
        self._service.stop_command(self.command_id)

    def start(self, *args, **kwargs):
        """
        Start running this command

        Returns:
            command id
        """
        return self.run(*args, **kwargs)

    def run(self, *args, **kwargs):
        """
        Runs the command async with *args and **kwargs.

        Returns:
            command id
        """
        self._ensure_service()
        self._args = args
        self._kwargs = kwargs
        log.d("Running command:", self.__class__.__name__)
        self._service.start_command(
            self.command_id, *self._args, **self._kwargs)
        return self.command_id


class _CommandPlugin:
    ""

    command_cls = None

    def __init__(self, name, *args, description='', **kwargs):
        self.name = name
        self._args_types = args
        self._kwargs_types = kwargs
        self._description = description

    def qualifiedname(self):
        "Returns Class.command name"
        return self.command_cls.__name__ + '.' + self.name

    def invoke_on_plugins(self, *args, **kwargs):
        "Invoke all plugins"
        self._check_types(*args, **kwargs)
        return plugins.registered.call_command(
            self.qualifiedname(), *args, **kwargs)

    def _ensure_class(self, type1, type2):
        if isclass(type1):
            return issubclass(type1, type2)
        return False

    def _check_types(self, *args, **kwargs):
        tr = []
        tr.append(len(args) == len(self._args_types))
        tr.append(all(isinstance(y, x) or self._ensure_class(y, x)
                      for x, y in zip(self._args_types, args)))

        tr.append(all(x in self._kwargs_types for x in kwargs))
        tr.append(all(isinstance(kwargs[x], self._kwargs_types[x]) or self._ensure_class(kwargs[x], self._kwargs_types[x])
                      for x in kwargs if x in self._kwargs_types))
        if not all(tr):
            raise exceptions.CommandError(
                utils.this_function(),
                "Wrong types were used for command '{}'. Types used {}, types expected {}".format(
                    self.qualifiedname(),
                    self._stringify_args(args, kwargs),
                    self._stringify_args(self._args_types, self._kwargs_types, True)))

    def _stringify_args(self, args, kwargs, is_type=False):
        ""
        s = '('
        if is_type:
            s += ", ".join(str(x) for x in args)
            s += ", ".join(x + '=' + str(y) for x, y in kwargs.items())
        else:
            s += ", ".join(str(type(x)) for x in args)
            s += ", ".join(x + '=' + str(type(y)) for x, y in kwargs.items())

        s += ')'

        return s


class CommandEvent(_CommandPlugin):
    "Base command event"

    def __init__(self, name, *args, **kwargs):
        super().__init__(name, *args, **kwargs)

    def emit(self, *args, **kwargs):
        "emit this event with *args and **kwargs"
        self.invoke_on_plugins(*args, **kwargs)


class CommandEntry(_CommandPlugin):
    "Base command entry"

    def __init__(self, name, return_type, *args, **kwargs):
        super().__init__(name, *args, **kwargs)
        self.return_type = return_type
        self.default_handler = None
        self.default_capture_handlers = []

    def default(self, capture=False):
        "Set a default handler. Only one default handler is allowed"

        def wrapper(func):
            if capture:
                self.default_capture_handlers.append(func)
                return func

            if self.default_handler:
                raise exceptions.CommandError(
                    utils.this_function(),
                    "Command '{}' has already been assigned a default handler".format(
                        self.name))
            self.default_handler = func
            return func
        return wrapper

    @contextmanager
    def call_capture(self, token, *args, **kwargs):
        "Calls associated handlers with a capture token"
        handler = self.invoke_on_plugins(*args, **kwargs)
        handler.default_handler = self.default_handler
        handler.expected_type = self.return_type
        handler.capture = True
        handler.capture_token = token
        for h in self.default_capture_handlers:
            handler._add_capture_handler(h)
        yield handler

    @contextmanager
    def call(self, *args, **kwargs):
        "Calls associated handlers"
        handler = self.invoke_on_plugins(*args, **kwargs)
        handler.default_handler = self.default_handler
        handler.expected_type = self.return_type
        yield handler


def init_commands():
    CoreCommand._native_pool = ThreadPool(constants.maximum_native_workers)
