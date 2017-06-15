from contextlib import contextmanager
from abc import ABCMeta, abstractmethod

from happypanda.common import constants, utils, hlogger, exceptions
from happypanda.server.core import plugins

log = hlogger.Logger(__name__)

def get_available_commands():
    subs = utils.all_subclasses(Command)
    commands = set()
    for c in subs:
        c._get_commands()
        for a in c._entries:
            commands.add(c.__name__+'.'+c._entries[a].name)
    return commands
    
class Command:
    "Base command"

    _metaclass__ = ABCMeta

    _events = {}
    _entries = {}

    def __init__(self, **kwargs):
        self._get_commands()

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


    @abstractmethod
    def main(self, *args, **kwargs):
        pass

    def run(self, *args, **kwargs):
        """
        Run the command with *args and **kwargs.
        """
        log.d("Running command: ", self.__name__)
        self.main(*args, **kwargs)

class UndoCommand(Command):
    "Command capable of undoing itself"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @abstractmethod
    def undo(self):
        pass

class _CommandPlugin:
    ""

    command_cls = None

    def __init__(self, name, *args, description='', **kwargs):
        self.name = name
        self._args_types = args
        self._kwargs_types = kwargs
        self._description = description

    def invoke_on_plugins(self, *args, **kwargs):
        "Invoke all plugins"
        self._check_types(*args, **kwargs)
        return constants.plugin_manager.call_command(
            self.command_cls.__name__+'.'+self.name, *args, **kwargs)

    def _check_types(self, *args, **kwargs):
        tr = []
        tr.append(len(args) == len(self._args_types))
        tr.append(all(isinstance(x, y) for x, y in zip(self._args_types, args)))
        tr.append(all(x in self._kwargs_types for x in kwargs))
        tr.append(all(isinstance(args[x], self._kwargs_types[x]) for x in args if x in self._kwargs_types))
        if not all(tr):
            raise exceptions.CoreError(utils.this_function(), "Wrong types were used for this command")


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
        self._handler_value = None
        self._called = False

    def __getattr__(self, name):
        # TODO: maybe find a less hacky way?
        if hasattr(self._handler_value, name):
            if not self._called:
                raise exceptions.CoreError("Command has not yet been called")
            use_default = False

            func = getattr(self._handler_value, name)
            try:
                v = func()
            except exceptions.PluginError as e:
                use_default = True
                if e.node:
                    logger = e.node.logger
                else:
                    logger = log

                logger.exception("An unhandled plugin exception has occured")
        else:
            raise AttributeError("HandlerValue has no attribute '{}'".format(name))

    @contextmanager
    def call(self, *args, **kwargs):
        ""
        self._called = True
        self._handler_value = self.invoke_on_plugins(*args, **kwargs)
        yield self
