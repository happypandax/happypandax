import gevent
import weakref
import functools
import itertools

from gevent import pool, queue
from apscheduler.schedulers.gevent import GeventScheduler

from happypanda.common import hlogger, constants, config
from happypanda.core import command, async

log = hlogger.Logger(__name__)


class Service:

    generic = None
    _id_counter = itertools.count(100)

    services = []
    _all_commands = {}

    def __init__(self, name):
        self.name = name
        self.services.append(weakref.ref(self))

    def add_command(self, cmd):
        command_id = next(self._id_counter)
        cmd.command_id = command_id
        cmd.service = self
        self._all_commands[command_id] = weakref.ref(cmd)
        return command_id

    def start_command(self, cmd_id, *args, **kwargs):
        pass

    def stop_command(self, cmd_id):
        pass

    @classmethod
    def get_command(cls, cmd_id):
        if cmd_id in cls._all_commands:
            return cls._all_commands[cmd_id]()
        return None

#@attr.s
# class Trigger:
#    ""
#    _start = attr.ib(None)
#    _every = attr.ib(None)
#    _day = attr.ib(None)
#    _year = attr.ib(None)
#    _month = attr.ib(None)
#    _hour = attr.ib(None)
#    _minute = attr.ib(None)
#    _second = attr.ib(None)
#    _monday = attr.ib(None)
#    _tuesday = attr.ib(None)
#    _wednesday = attr.ib(None)
#    _thursday = attr.ib(None)
#    _friday = attr.ib(None)
#    _saturday = attr.ib(None)
#    _sunday = attr.ib(None)

#    def __attrs_post_init__(self):
#        self._committed = False

#    @property
#    def _d(self):
#        d = attr.asdict(self)
#        d.pop('_start')
#        return d

#    @property
#    def _t(self):
#        t = list(attr.astuple(self))
#        return tuple(l[1:])

#    def at(self, date):
#        ""
#        return self

#    def every(self, interval):
#        assert self._every is None, "Cannot call every twice"
#        ""
#        self._every = interval
#        return self

#    @property
#    def second(self):
#        assert self._second is None, "Can only call second once"
#        self._second = True
#        return self

#    @property
#    def minute(self):
#        assert self._minute is None, "Can only call minute once"
#        self._minute = True
#        return self

#    @property
#    def hour(self):
#        self._hour = True
#        return self

#    @property
#    def day(self):
#        self._day = True
#        return self

#    @property
#    def month(self):
#        self._month = True
#        return self

#    @property
#    def year(self):
#        self._year = True
#        return self

#    @property
#    def monday(self):
#        self._monday = True
#        return self

#    @property
#    def tuesday(self):
#        self._tuesday = True
#        return self

#    @property
#    def wednesday(self):
#        self._wednesday = True
#        return self

#    @property
#    def thursday(self):
#        self._thursday = True
#        return self

#    @property
#    def friday(self):
#        self._friday = True
#        return self

#    @property
#    def saturday(self):
#        self._saturday = True
#        return self

#    @property
#    def sunday(self):
#        self._sunday = True
#        return self


class Scheduler(Service):
    """
    Service running scheduled and periodic commands
    """

    def __init__(self, name):
        super().__init__(name)
        self._scheduler = GeventScheduler({
            'apscheduler.timezone': 'UTC', # TODO: locatime or user configurable
        })
        self._jobstores = {}
        self._executors = {}
        self._job_defaults = {}
        self._jobs = {}  # cmd_id : job
        self._triggers = {}  # cmd_id : trigger

    def start(self):
        "Start the scheduler"
        self._scheduler.start()
        log.d("Started scheduler service:", self.name)
        return self

    def add_command(self, cmd, trigger=None):
        "Add a command to this scheduler and return a command id"
        assert isinstance(cmd, command.CoreCommand)
        command_id = super().add_command(cmd)
        if trigger:
            self.set_trigger(command_id, trigger)
        else:
            raise NotImplementedError
        return command_id

    def set_trigger(self, cmd_id, trigger):
        "Change the trigger for a command in this scheduler"
        self._triggers[cmd_id] = trigger

    def remove_command(self, cmd_id):
        "Remove a command from this scheduler"
        raise NotImplementedError

    def pause_command(self, cmd_id):
        "Pause a command in this scheduler, returns command state"
        raise NotImplementedError

    def resume_command(self, cmd_id):
        "Resume a command in this scheduler, returns command state"
        raise NotImplementedError

    def start_command(self, cmd_id, *args, **kwargs):
        "Start running a command in this scheduler, returns command state"
        cmd = self.get_command(cmd_id)
        self._jobs[cmd_id] = self._scheduler.add_job(cmd._run,
                                                     self._triggers[cmd_id],
                                                     args, kwargs,
                                                     name=cmd.__class__.__name__)

    def stop_command(self, cmd_id):
        "alias for remove_command"
        self.remove_command(cmd_id)

    def shutdown(self, wait=False):
        "Shutdown scheduler"
        self._scheduler.shutdown(wait=wait)
        return self

    def pause(self):
        "Pause scheduler"
        raise NotImplementedError
        return self

    def resume(self):
        "Resume scheduler"
        raise NotImplementedError
        return self


class AsyncService(Service):
    """
    Service running asynchronous commands
    """

    _all_commands = {}

    def __init__(self, name, group=pool.Group()):
        super().__init__(name)
        self._commands = {}  # cmd_id : command
        self._greenlets = {}  # cmd_id : greenlet
        self._decorators = {}  # cmd_id : callable
        self._group = group
        self._queue = queue.Queue()

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
            command_id = super().add_command(cmd)
            self._commands[command_id] = cmd
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
                self._commands[cmd_id]._run, *args, **kwargs)

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


class NetworkService(AsyncService):
    "A network service"

    def __init__(self, name, pool_=None):
        super().__init__(name, pool_ or pool.Pool(config.concurrent_network_tasks.value * 2))


class DownloadService(AsyncService):
    "A download service"

    def __init__(self, name):
        super().__init__(name, pool.Pool(config.concurrent_network_tasks.value))


class ImageService(AsyncService):
    "An image service"

    def __init__(self, name):
        super().__init__(name, pool.Pool(config.concurrent_image_tasks.value))


def init_generic_services():
    Scheduler.generic = Scheduler("generic")
    AsyncService.generic = AsyncService("generic")
    NetworkService.generic = NetworkService("network")
    DownloadService.generic = DownloadService("download")
    ImageService.generic = ImageService("image")
