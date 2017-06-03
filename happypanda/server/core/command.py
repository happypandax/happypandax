from gevent import pool
from contextlib import contextmanager
from abc import ABCMeta, abstractmethod

from happypanda.common import constants, utils
from happypanda.server.core import plugins

log = utils.Logger(__name__)

def get_available_commands():
    subs = utils.all_subclasses(Command)
    commands = []
    for c in subs:
        c._get_commands()
        for a in c._entries:
            commands.append(c.__name__+'.'+a.name)
    return commands
    
class CommandRunner:
    ""

    def __init__(self, amount_of_tasks=constants.allowed_tasks):
        self._pool = pool.Pool(amount_of_tasks)
        self._commands = {}
        self._command_id = 0

    def run(self, command, *args, **kwargs):
        "Run a command async, returns id"
        assert isinstance(command, Command)

        self._command_id += 1
        task_id = self._command_id
        self._commands[task_id] = self._pool.spawn(command.run, *args, **kwargs)
        return task_id

    def command_done(self, command_id):
        ""
        if command_id in self._commands:
            return self._commands[command_id].ready()
        return True

    def get_value(self, command_id):
        ""
        if self.command_done(command_id):
            return self._commands[command_id].value()

class Command:
    "Base command"

    _metaclass__ = ABCMeta

    _runner = CommandRunner()

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
    def run(self, *args, **kwargs):
        pass

    def execute(self, *args, sync=True, **kwargs):
        
        if sync:
            pass
        else:
            self._runner.run(self.run, *args, **kwargs)

class UndoCommand(Command):
    "Command capable of undoing itself"

    def undo(self):
        pass


class _CommandPlugin:
    ""

    command_cls = None

    def __init__(self):
        self.name = ''

    def invoke_on_plugins(self, *args, **kwargs):
        "Invoke all plugins"
        return constants.plugin_manager.on_command(
            self.command_cls.__name__+'.'+self.name, *args, **kwargs)



class CommandEvent(_CommandPlugin):
    "Base command event"

    def __init__(self, name):
        super().__init__()
        self.name = name

    def emit(self, *args, **kwargs):
        "emit event"
        self.invoke_on_plugins(*args, **kwargs)

class CommandEntry(_CommandPlugin):
    "Base command entry"

    def __init__(self, name, return_type):
        super().__init__()
        self.name = name
        self.return_type = return_type

    @contextmanager
    def call(self, *args, **kwargs):
        ""

