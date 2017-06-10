from contextlib import contextmanager
from abc import ABCMeta, abstractmethod

from happypanda.common import constants, utils, hlogger
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

    _runner = CommandRunner()
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

    def run(self, *args, sync=True, **kwargs):
        """
        Run the command with *args and **kwargs.
        Returns command retunobject if sync is true else returns a TaskID
        """
        if sync:
            pass
        else:
            self._runner.main(self.run, *args, **kwargs)

class UndoCommand(Command):
    "Command capable of undoing itself"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def undo(self):
        pass


class _CommandPlugin:
    ""

    command_cls = None

    def __init__(self, name):
        self.name = name

    def invoke_on_plugins(self, *args, **kwargs):
        "Invoke all plugins"
        return constants.plugin_manager.on_command(
            self.command_cls.__name__+'.'+self.name, *args, **kwargs)



class CommandEvent(_CommandPlugin):
    "Base command event"

    def __init__(self, name):
        super().__init__(name)

    def emit(self, *args, **kwargs):
        "emit this event with *args and **kwargs"
        self.invoke_on_plugins(*args, **kwargs)

class CommandEntry(_CommandPlugin):
    "Base command entry"

    def __init__(self, name, return_type):
        super().__init__(name)
        self.return_type = return_type

    @contextmanager
    def call(self, *args, **kwargs):
        ""
        yield self.invoke_on_plugins(*args, **kwargs)
