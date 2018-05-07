import enum
import arrow
import gevent
import weakref
import sys
import itertools

from contextlib import contextmanager
from abc import ABCMeta, abstractmethod
from inspect import isclass
from gevent.threadpool import ThreadPool
from cachetools import LRUCache
from treelib import Tree, exceptions as tree_exceptions

from happypanda.common import utils, hlogger, exceptions, constants
from happypanda.core import plugins, async_utils, db

log = hlogger.Logger(constants.log_ns_command + __name__)


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


def _native_runner(f):

    def cleanup_wrapper(*args, **kwargs):
        with db.cleanup_session():
            r = f(*args, **kwargs)
        return r

    parent = weakref.proxy(gevent.getcurrent())
    frame = sys._getframe()

    def wrapper(*args, **kwargs):
        log.d("Running", f, "in native thread")
        if utils.get_context(None) is None:
            g = gevent.getcurrent()
            try:
                g._hp_inherit(parent, frame)
            except AttributeError:
                async_utils.Greenlet._hp_inherit(g, parent, frame)
        return cleanup_wrapper(*args, **kwargs)
    return wrapper


class CoreCommand:
    "Base command"

    _events = {}
    _entries = {}
    _native_pool = None
    _progress_counter = itertools.count(1)
    _progresses = LRUCache(500)

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
        self._progress_max = None
        self._progress_current = None
        self._progress_text = None
        self._progress_count = None
        self._progress_type = None
        self._progress_tree = None
        self._progress_time = None
        self._progress_timestamp = 0
        self._progress_title = self.__class__.__name__

    def _run(self, *args, **kwargs):
        """
        Run the command with *args and **kwargs.
        """
        log.d("Running command:", self.__class__.__name__)
        r = self.main(*args, **kwargs)
        log.d("Finished running command:", self.__class__.__name__)
        return r

    @classmethod
    def get_all_progress(cls):
        ps = []
        for c, t in cls._progresses.items():
            x = t.get_node(t.root).data()
            if x:
                ps.insert(0, x.get_progress())
        return ps

    def _add_progress(self, add=True):
        if not self._progress_count:
            self._progress_count = next(self._progress_counter)

        if self._progress_tree is None and self._progress_count not in self._progresses:
            self._progress_tree = Tree()
            if add:
                self._progresses[self._progress_count] = self._progress_tree
            self._progress_tree.create_node(self._progress_count, self._progress_count, data=weakref.ref(self))
            self._progress_timestamp = arrow.now().timestamp

        self._progress_time = arrow.now()

    def merge(self, cmd):
        ""
        assert cmd is None or isinstance(cmd, CoreCommand)
        if cmd:
            self.merge_progress_into(cmd)
        return self

    def merge_progress_into(self, cmd):
        assert isinstance(cmd, CoreCommand)
        cmd._add_progress()
        self._add_progress(False)
        cmd._progress_tree.paste(cmd._progress_count, self._progress_tree)

        self._progress_tree = cmd._progress_tree

        if self._progress_count in self._progresses:
            del self._progresses[self._progress_count]

    def _str_progress_tree(self):
        self._tree_reader = ""

        def w(l):
            self._tree_reader = l.decode('utf-8') + '\n'

        try:
            self._progress_tree._Tree__print_backend(func=w)
        except tree_exceptions.NodeIDAbsentError:
            self._tree_reader = "Tree is empty"
        return self._tree_reader

    def get_progress(self):

        if self._progress_tree:
            log.d("Command", self, "progress tree:\n{}".format(self._str_progress_tree()))
            p = {'title': self._progress_title,
                 'subtitle': '',
                 'subtype': None,
                 'text': '',
                 'value': .0,
                 'percent': .0,
                 'max': .0,
                 'type': self._progress_type,
                 'timestamp': self._progress_timestamp}

            t = self._progress_tree.subtree(self._progress_count)
            prog_time = self._progress_time
            prog_text = self._progress_text if self._progress_text else ''
            prog_subtitle = ''
            prog_subtype = None
            for _, n in t.nodes.items():
                cmd = n.data()
                if cmd:
                    if cmd._progress_max:
                        p['max'] += cmd._progress_max
                    if cmd._progress_current:
                        p['value'] += cmd._progress_current

                    if not prog_time or (cmd._progress_time and cmd._progress_time > prog_time):
                        prog_text = cmd._progress_text
                        prog_subtitle = cmd._progress_title
                        prog_subtype = cmd._progress_type
            if p['max']:
                p['percent'] = (100 / p['max']) * p['value']
            else:
                p['percent'] = -1.0
            p['text'] = prog_text
            p['subtitle'] = prog_subtitle
            p['subtype'] = prog_subtype
            return p
        return None

    def set_progress(self, value=None, text=None, title=None, type_=None):
        assert value is None or isinstance(value, (int, float))
        assert text is None or isinstance(text, str)
        assert title is None or isinstance(text, str)
        self._add_progress()
        if title is not None:
            self._progress_title = title
        if value is not None:
            self._progress_current = value
        if text is not None:
            self._progress_text = text
        if type_ is not None:
            self._progress_type = type_

    def set_max_progress(self, value):
        assert isinstance(value, (int, float))
        self._add_progress()
        self._progress_max = value

    def next_progress(self, add=1, text=None, _from=0):
        assert isinstance(add, (int, float))
        if self._progress_current is None:
            self._progress_current = _from
        if text is not None:
            self._progress_text = text
        self._progress_current += add

    @contextmanager
    def progress(self, max_progress=None, text=None):
        if max_progress is not None:
            self.set_max_progress(max_progress)
        yield
        if max_progress is not None:
            self.set_progress(max_progress, text)

    def run_native(self, f, *args, **kwargs):
        f = async_utils.AsyncFuture(self, self._native_pool.apply_async(_native_runner(f), args, kwargs))
        self._futures.append(f)
        return f

    def push(self, msg, scope=None):
        if constants.notification:
            return constants.notification.push(msg, scope=scope)
        # TODO: raise error perhaps?

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

    def __del__(self):
        if self._progress_count and self._progress_count in self._progresses:
            del self._progresses[self._progress_count]

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
        return self._run(*args, **kwargs)

    def _main(self):
        pass

    def _main_wrap(self, *args, **kwargs):
        utils.switch(self._priority)
        self._started_time = arrow.now()
        log.d("Calling main function of command:", self.__class__.__name__)
        r = self._main(*args, **kwargs)
        if self._progress_max is not None:
            self.set_progress(self._progress_max)
        if self._progress_count and self._progress_count in self._progresses:
            gevent.spawn_later(
                constants.command_progress_removal_time,
                lambda: self._progresses.pop(
                    self._progress_count))
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
        return constants.plugin_manager._call_command(
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
        self._handlers = set()

    def emit(self, *args, **kwargs):
        "emit this event with *args and **kwargs"
        self.invoke_on_plugins(*args, **kwargs)
        for h in self._handlers:
            h(*args, **kwargs)

    def subscribe(self, handler):
        "subscribe to event with callable"
        assert callable(handler)
        self._handlers.add(handler)

    def remove(self, handler):
        "remove previously added handler"
        self._handlers.remove(handler)


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
        log.d("Calling command handler <{}> [{}]".format(self.qualifiedname(), token))
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
        log.d("Calling command handler <{}>".format(self.qualifiedname()))
        handler = self.invoke_on_plugins(*args, **kwargs)
        handler.default_handler = self.default_handler
        handler.expected_type = self.return_type
        yield handler


def init_commands():
    CoreCommand._native_pool = ThreadPool(constants.maximum_native_workers)
