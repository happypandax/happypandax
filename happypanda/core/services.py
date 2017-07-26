import gevent
import weakref
import itertools
import functools

from gevent import pool, queue

from happypanda.common import hlogger, constants
from happypanda.core import command

log = hlogger.Logger(__name__)


class Service:

    services = []
    generic = None
    _id_counter = itertools.count(100)
    _all_commands = {}

    def __init__(self, name, group=pool.Group()):
        self.name = name
        self._commands = {}  # cmd_id : command
        self._greenlets = {}  # cmd_id : greenlet
        self._decorators = {}  # cmd_id : callable
        self._group = group
        self._queue = queue.Queue()
        self.services.append(weakref.ref(self))

    def wait_all(self, timeout=None):
        "Wait for all commands to finish running and then return True, else False"
        log.d("Service is waiting for all tasks")
        return self._group.join(timeout)

    def add_command(self, cmd, decorater=None):
        "Add a command to this service and return a command id"
        assert isinstance(cmd, command.AsyncCommand)
        assert callable(decorater) or decorater is None
        if cmd not in self._commands.values():
            command_id = next(self._id_counter)
            cmd.command_id = command_id
            cmd.service = self
            self._commands[command_id] = cmd
            self._all_commands[command_id] = weakref.ref(cmd)
            if decorater:
                self._decorators[command_id] = decorater
            log.d(
                "Service ({})".format(
                    self.name),
                "added command:",
                cmd.__class__.__name__,
                "({})".format(command_id))
            cmd.state = command.CommandState.in_service
            return command_id
        else:  # TODO: abit nonsensical? raise error instead maybe
            for c_id in self._commands:
                if self._commands[c_id] == cmd:
                    return c_id

    def start_command(self, cmd_id, *args, _callback=None, **kwargs):
        """
        Start running a specific command by its command id
        """
        assert isinstance(cmd_id, int)

        if cmd_id not in self._greenlets:
            self._greenlets[cmd_id] = gevent.Greenlet(
                self._commands[cmd_id].main, *args, **kwargs)

        green = self._greenlets[cmd_id]

        green.link(
            functools.partial(
                self._callback_wrapper,
                cmd_id,
                self._commands[cmd_id],
                _callback))

        self._start(cmd_id)

    def stop_command(self, cmd_id):
        """
        Stop running a specific command by its command id
        """
        assert isinstance(cmd_id, int)

        if cmd_id in self._greenlets:
            self._greenlets[cmd_id].kill()

    def get_command_value(self, cmd_id):
        """
        Get returned value of command by its command id
        """
        assert isinstance(cmd_id, int)
        if cmd_id in self._greenlets:
            return self._greenlets[cmd_id].value

    @classmethod
    def get_command(cls, cmd_id):
        if cmd_id in cls._all_commands:
            return cls._all_commands[cmd_id]()
        return None

    def _callback_wrapper(self, command_id, command_obj, callback, greenlet):
        assert callable(callback) or callback is None

        if not self._queue.empty():
            try:
                next_cmd_id = self._queue.get_nowait()
                log.d("Starting command id", next_cmd_id, " next in queue in service '{}'".format(self.name))
                self._start(next_cmd_id)
            except queue.Empty:
                pass

        command_obj.state = command.CommandState.finished
        try:
            greenlet.get()
        except:
            log.exception("Command", "{}({})".format(command_obj.__class__.__name__, command_id), "raised an exception")
            command_obj.state = command.CommandState.failed
            command_obj.exception = greenlet.exception

        if isinstance(greenlet.value, gevent.GreenletExit):
            command_obj.state = command.CommandState.stopped
            greenlet.value = None

        if command_id in self._decorators:
            greenlet.value = self._decorators[command_id](greenlet.value)

        log.d(
            "Command id", command_id, "in service '{}'".format(
                self.name), "has finished running with state:", str(
                command_obj.state))

        if callback:
            callback(greenlet.value)

    def _start(self, cmd_id):

        if not self._group.full():
            self._group.start(self._greenlets[cmd_id])
            self._commands[cmd_id].state = command.CommandState.started
        else:
            self._queue.put(cmd_id)
            self._commands[cmd_id].state = command.CommandState.in_queue
            log.d("Enqueueing command id", cmd_id, "in service '{}'".format(self.name))


Service.generic = Service("generic")


class DownloadItem(command.AsyncCommand):

    def __init__(self, service, url, session=None):
        assert isinstance(service, DownloadService)
        super().__init__(service)
        self.session = session
        self.url = url
        self.file = ""
        self.name = ""


class DownloadService(Service):
    "A download service"

    def __init__(self, name):
        super().__init__(name)

DownloadService.generic = DownloadService("download")


class ImageService(Service):
    "An image service"

    def __init__(self, name):
        super().__init__(name, pool.Pool(constants.concurrent_image_tasks))

ImageService.generic = ImageService("image")
