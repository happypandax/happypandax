import gevent
import weakref
import functools
import itertools

from gevent import pool, queue
from apscheduler.schedulers.gevent import GeventScheduler

from happypanda.common import hlogger, constants, config
from happypanda.core import command, async

log = hlogger.Logger(__name__)

class SchedulerJob:
    ""

    def __init__(self, _job, _scheduler):
        self._job = _job
        self._scheduler = _scheduler


class Scheduler:
    generic = None

    def __init__(self, name):
        self._scheduler = None
        self._jobstores = {}
        self._executors = {}
        self._job_defaults = {}

    def init(self):
        "Initialize the scheduler"

        self._scheduler = GeventScheduler()
        return self

    def start(self):
        "Start the scheduler"
        if self._scheduler:
            self._scheduler.start()
        return self

    def add_command(self, cmd):
        "Add a command to this scheduler and return a command id"
        assert isinstance(cmd, command.CoreCommand)

    def remove_command(self, cmd):
        "Remove a command from this scheduler"
        raise NotImplementedError
        assert isinstance(cmd, command.CoreCommand)

    def pause_command(self, cmd):
        "Pause a command in this scheduler"
        raise NotImplementedError
        assert isinstance(cmd, command.CoreCommand)

    def resume_command(self, cmd):
        "Resume a command in this scheduler"
        raise NotImplementedError
        assert isinstance(cmd, command.CoreCommand)

    def shutdown(self, wait=False):
        "Shutdown scheduler"
        if self._scheduler:
            self._scheduler.shutdown(wait=wait)

    def pause(self):
        "Pause scheduler"
        raise NotImplementedError
        pass

    def resume(self):
        "Resume scheduler"
        raise NotImplementedError



class Service:

    services = []
    generic = None
    _all_commands = {}
    _id_counter = itertools.count(100)

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
        gevent.idle(constants.Priority.Normal.value)
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
        gevent.idle(constants.Priority.Normal.value)
        if cmd_id not in self._greenlets:
            self._greenlets[cmd_id] = async.Greenlet(
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
        gevent.idle(constants.Priority.Normal.value)
        if cmd_id in self._greenlets:
            self._commands[cmd_id].kill()
            self._greenlets[cmd_id].kill()

    def get_command_value(self, cmd_id):
        """
        Get returned value of command by its command id
        """
        assert isinstance(cmd_id, int)
        gevent.idle(constants.Priority.Normal.value)
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
        except BaseException:
            log.exception("Command", "{}({})".format(command_obj.__class__.__name__, command_id), "raised an exception")
            command_obj.state = command.CommandState.failed
            command_obj.exception = greenlet.exception
            if constants.dev:
                raise  # doesnt work
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
        gevent.idle(constants.Priority.Low.value)
        if not self._group.full():
            self._group.start(self._greenlets[cmd_id])
            self._commands[cmd_id].state = command.CommandState.started
        else:
            self._queue.put(cmd_id)
            self._commands[cmd_id].state = command.CommandState.in_queue
            log.d("Enqueueing command id", cmd_id, "in service '{}'".format(self.name))

class NetworkService(Service):
    "A network service"

    def __init__(self, name, pool_=None):
        super().__init__(name, pool_ or pool.Pool(config.concurrent_network_tasks.value*2))

class DownloadService(NetworkService):
    "A download service"

    def __init__(self, name):
        super().__init__(name, pool.Pool(config.concurrent_network_tasks.value))


class ImageService(Service):
    "An image service"

    def __init__(self, name):
        super().__init__(name, pool.Pool(config.concurrent_image_tasks.value))


def init_generic_services():
    Service.generic = Service("generic")
    NetworkService.generic = NetworkService("network")
    DownloadService.generic = DownloadService("download")
    ImageService.generic = ImageService("image")
