import gevent
import weakref
import functools
import itertools
import pytz

from gevent import pool, queue, event
from apscheduler.schedulers.gevent import GeventScheduler
#from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from cachetools import LRUCache

from happypanda.common import hlogger, constants, config, exceptions, utils, clsutils
from happypanda.core import command, async_utils, db
from happypanda.interface.enums import CommandState

log = hlogger.Logger(constants.log_ns_command + __name__)


class Service:

    generic = None
    _id_counter = itertools.count(100)

    _all_commands = weakref.WeakValueDictionary()

    def __init__(self, name):
        self.name = name
        constants.services[self.identifier()] = self

    def identifier(self):
        return f"{self.__class__.__name__.lower()}.{self.name.lower()}"

    def add_command(self, cmd):
        command_id = next(self._id_counter)
        cmd.command_id = command_id
        cmd.service = self
        self._all_commands[command_id] = cmd
        return command_id

    def start_command(self, cmd_id, *args, **kwargs):
        pass

    def stop_command(self, cmd_id):
        pass

    @classmethod
    def get_command(cls, cmd_id):
        if cmd_id in cls._all_commands:
            return cls._all_commands[cmd_id]
        return None

# class Trigger:
#    """
#    [start.[every/at].[time/day/month...].[at]]
#    """

#    def __init__(self, start=None):
#        self._reset()
#        self._start = start
#        self._committed = False
#        self._at_1_date = None
#        self._at_2_date = None
#        self._on = None
#        self._repeat = None


#    @property
#    def _d(self):
#        d = attr.asdict(self)
#        d.pop('_start')
#        return d

#    @property
#    def _t(self):
#        t = list(attr.astuple(self))
#        return tuple(l[1:])

#    def _reset(self):
#        self._every = None
#        self._day = None
#        self._year = None
#        self._month = None
#        self._hour = None
#        self._minute = None
#        self._second = None
#        self._monday = None
#        self._tuesday = None
#        self._wednesday = None
#        self._thursday = None
#        self._friday = None
#        self._saturday = None
#        self._sunday = None

#    def at(self, date):
#        ""
#        assert isinstance(date, (arrow.Arrow, ))
#        if self._on is None:
#            self._at_1_date = date
#        else:
#            self._at_2_date = date

#        return self

#    def every(self, interval):
#        assert self._every, "Cannot call every twice"
#        ""
#        self.every = True
#        self._repeat = interval
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
#        assert self._hour is None, "Can only call hour once"
#        self._hour = True
#        return self

#    @property
#    def day(self):
#        assert self._day is None, "Can only call day once"
#        self._day = True
#        return self

#    @property
#    def month(self):
#        assert self._month is None, "Can only call month once"
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

#    def _compile(self):
#        if self._day:
#            pass
#        self._year = None
#        self._month = None
#        self._hour = None
#        self._minute = None
#        self._second = None


#        self._monday = None
#        self._tuesday = None
#        self._wednesday = None
#        self._thursday = None
#        self._friday = None
#        self._saturday = None
#        self._sunday = None


class Scheduler(Service):
    """
    Service running scheduled and periodic commands
    """

    _schedulers = weakref.WeakSet()

    def __init__(self, name):
        super().__init__(name)
        self._commands = {}  # cmd_id : command
        # self._jobstores = {'default': SQLAlchemyJobStore(url=constants.scheduler_database_url,
        #                                                 tablename="jobs")}
        self._jobstores = {}
        self._executors = {}
        self._job_defaults = {
            'max_instances': 10,
            'coalesce': True,
        }
        self._triggers = {}  # cmd_id : trigger
        self._scheduler = GeventScheduler(jobstores=self._jobstores,
                                          executors=self._executors,
                                          job_defaults=self._job_defaults,
                                          timezone=pytz.utc,  # TODO: make user configurable
                                          )
        self._schedulers.add(self)
        s_cmds = constants.internaldb.scheduler_commands.get({})
        v = s_cmds.setdefault(self.identifier(), {})
        if not v:
            constants.internaldb.scheduler_commands.set(s_cmds)

    def _get_job_id(self, cmd_id):
        s_cmds = constants.internaldb.scheduler_commands.get()
        return s_cmds[self.identifier()].get(cmd_id)

    def _set_job_id(self, cmd_id, job_id):
        if not isinstance(job_id, int):
            job_id = job_id.id
        s_cmds = constants.internaldb.scheduler_commands.get()
        s_cmds[self.identifier()][cmd_id] = job_id
        constants.internaldb.scheduler_commands.set(s_cmds)

    def start(self):
        "Start the scheduler"
        self._scheduler.start()
        log.d("Started scheduler service:", self.name)
        return self

    def add_command(self, cmd, trigger=None):
        "Add a command to this scheduler and return a command id"
        assert isinstance(cmd, command.CoreCommand)
        command_id = super().add_command(cmd)
        self._commands[command_id] = cmd
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
        j_id = self._get_job_id(cmd_id)
        self._scheduler.remove_job(j_id)

    def pause_command(self, cmd_id):
        "Pause a command in this scheduler, returns command state"
        raise NotImplementedError

    def resume_command(self, cmd_id):
        "Resume a command in this scheduler, returns command state"
        raise NotImplementedError

    def start_command(self, cmd_id, *args, **kwargs):
        "Start running a command in this scheduler, returns command state"
        cmd = self.get_command(cmd_id)
        j_id = self._scheduler.add_job(cmd._run,
                                       self._triggers[cmd_id],
                                       args, kwargs,
                                       name=cmd.__class__.__name__)
        self._set_job_id(cmd_id, j_id)

    def stop_command(self, cmd_id):
        "alias for remove_command"
        self.remove_command(cmd_id)

    def shutdown(self, wait=True):
        "Shutdown scheduler"
        self._scheduler.shutdown(wait=wait)
        return self

    @classmethod
    def shutdown_all(cls, wait=True):
        "Shutdown all schedulers"
        for s in cls._schedulers:
            s.shutdown(wait=wait)

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

    _all_commands = LRUCache(10 * 1000)

    def __init__(self, name, group=pool.Group()):
        super().__init__(name)
        self._commands = {}  # cmd_id : command
        self._greenlets = {}  # cmd_id : greenlet
        self._values = {}  # cmd_id : values
        self._decorators = {}  # cmd_id : callable
        self._group = group
        self._queue = queue.Queue()

    def wait_all(self, timeout=None):
        "Wait for all commands to finish running and then return True, else False"
        log.d("Service is waiting for all tasks")
        return self._group.join(timeout)

    def add_command(self, cmd, decorator=None):
        "Add a command to this service and return a command id"
        gevent.idle(constants.Priority.Normal.value)
        assert isinstance(cmd, command.AsyncCommand)
        assert callable(decorator) or decorator is None
        if cmd not in self._commands.values():
            command_id = super().add_command(cmd)
            self._commands[command_id] = cmd
            if decorator:
                self._decorators[command_id] = decorator
            log.d(
                "Service ({})".format(
                    self.name),
                "added command:",
                cmd.__class__.__name__,
                "({})".format(command_id))
            cmd.state = CommandState.in_service
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
            self._greenlets[cmd_id] = async_utils.Greenlet(
                db.cleanup_session_wrap(self._commands[cmd_id]._run), *args, **kwargs)

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
            if cmd_id in self._commands:
                self._commands[cmd_id].kill()
            if cmd_id in self._greenlets:
                self._greenlets[cmd_id].kill()

    def get_command_value(self, cmd_id):
        """
        Get returned value of command by its command id
        """
        assert isinstance(cmd_id, int)
        gevent.idle(constants.Priority.Normal.value)
        if cmd_id in self._values:
            return self._values[cmd_id]

    def _callback_wrapper(self, command_id, command_obj, callback, greenlet):
        assert callable(callback) or callback is None
        try:
            if not self._queue.empty():
                try:
                    next_cmd_id = self._queue.get_nowait()
                    log.d("Starting command id", next_cmd_id, " next in queue in service '{}'".format(self.name))
                    self._start(next_cmd_id)
                except queue.Empty:
                    pass

            command_obj.state = CommandState.finished
            try:
                greenlet.get()
            except BaseException:
                log.exception(
                    "Command",
                    "{}({})".format(
                        command_obj.__class__.__name__,
                        command_id),
                    "raised an exception")
                command_obj.state = CommandState.failed
                command_obj.exception = greenlet.exception
                if constants.dev:
                    raise  # doesnt work
            value = greenlet.value
            if isinstance(value, gevent.GreenletExit):
                command_obj.state = CommandState.stopped
                value = None

            if command_id in self._decorators:
                value = self._decorators[command_id](value)

            self._values[command_id] = value

            log.d(
                "Command id", command_id, "in service '{}'".format(
                    self.name), "has finished running with state:", str(
                    command_obj.state))
            if callback:
                callback(value)
        except BaseException:
            log.exception()
            raise

    def _start(self, cmd_id):
        gevent.idle(constants.Priority.Low.value)
        if not self._group.full():
            self._group.start(self._greenlets[cmd_id])
            self._commands[cmd_id].state = CommandState.started
        else:
            self._queue.put(cmd_id)
            self._commands[cmd_id].state = CommandState.in_queue
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


class TaskService(Service):
    """
    A task service where tasks only run when woken up
    Results only reset when a task is woken up again
    """

    class TaskCommand:

        def __init__(self, cmd_id, service):
            self.command_id = cmd_id
            self.service = service

        def wake_up(self):
            self.service(self.command_id)

        def get(self, block=True, timeout=None):
            self.service.get_command_value(block=block, timeout=timeout)

    constants.task_command = clsutils.AttributeDict({
        "thumbnail_cleaner": None,
        "temp_cleaner": None,
    })

    def __init__(self, name):
        super().__init__(name)
        self._commands = {}  # cmd_id : command
        self._wake_objects = {}  # cmd_id : obj
        self._greenlets = {}  # cmd_id : greenlet
        self._values = {}  # cmd_id : values
        self._decorators = {}  # cmd_id : callable
        self._group = pool.Group()
        self._result_queue = queue.Queue()

        self._result_greenlet = self._group.start(async_utils.Greenlet(self._get_results))

    def add_command(self, cmd, decorator=None):
        "Add a command to this service and return a command id"
        gevent.idle(constants.Priority.Normal.value)
        assert isinstance(cmd, command.Command)
        assert callable(decorator) or decorator is None
        if cmd not in self._commands.values():
            command_id = super().add_command(cmd)
            self._commands[command_id] = cmd
            self._values[command_id] = None
            self._wake_objects[command_id] = event.Event()
            if decorator:
                self._decorators[command_id] = decorator
            log.d(
                "Service ({})".format(
                    self.name),
                "added command:",
                cmd.__class__.__name__,
                "({})".format(command_id))
            cmd.state = CommandState.in_service
            return command_id
        else:  # TODO: abit nonsensical? raise error instead maybe
            for c_id in self._commands:
                if self._commands[c_id] == cmd:
                    return c_id

    def start_command(self, cmd_id, *args, **kwargs):
        """
        Start running a specific command by its command id
        Returns a TaskCommand
        """
        assert isinstance(cmd_id, int)
        gevent.idle(constants.Priority.Normal.value)
        if cmd_id not in self._greenlets:
            self._greenlets[cmd_id] = async_utils.Greenlet(
                functools.partial(
                    self._command_wrapper,
                    cmd_id,
                    db.cleanup_session_wrap(self._commands[cmd_id].main),
                    self._wake_objects[cmd_id],
                    self._result_queue,
                ), args, kwargs)

        self._group.start(self._greenlets[cmd_id])
        return TaskService.TaskCommand(cmd_id, self)

    def _get_results(self):
        while True:
            cmd_id, r = self._result_queue.get()
            if self._values[cmd_id] is None:
                self._values[cmd_id] = event.AsyncResult()
            self._values[cmd_id].set(r)

    def _command_wrapper(self, cmd_id, cmd_main, wake_obj, result_queue, args, kwargs):
        while wake_obj.wait():
            try:
                r = cmd_main(*args, **kwargs)
                result_queue.put((cmd_id, r))
            except Exception as e:
                result_queue.put((cmd_id, e))
            wake_obj.clear()

    def stop_command(self, cmd_id):
        """
        Stop running a specific command by its command id
        """
        assert isinstance(cmd_id, int)
        gevent.idle(constants.Priority.Normal.value)
        if cmd_id in self._greenlets:
            if cmd_id in self._commands:
                self._commands[cmd_id].kill()
            if cmd_id in self._greenlets:
                self._greenlets[cmd_id].kill()

    def wake_up_command(self, cmd_id):
        """
        """
        if self._values[cmd_id] is None or self._values[cmd_id].ready():
            self._values[cmd_id] = event.AsyncResult()
        self._wake_objects[cmd_id].set()
        log.d("Waking up command", f"{cmd_id}:{self._commands[cmd_id].__class__.__name__}", "in", self.name, "service")

    def __call__(self, cmd_id):
        self.wake_up_command(cmd_id)

    def get_command_value(self, cmd_id, block=True, timeout=None):
        """
        Get returned value of command by its command id
        Timeout in seconds
        """
        assert isinstance(cmd_id, int)
        gevent.idle(constants.Priority.Normal.value)
        if self._values[cmd_id] is None:
            raise RuntimeError("Command hasn't been started yet")

        try:
            r = self._values[cmd_id].get(block=block, timeout=timeout)
        except gevent.Timeout as e:
            r = e
        if isinstance(r, gevent.Timeout):
            raise exceptions.TimeoutError(utils.this_function(), "Command value retrieval timed out")
        return r


def setup_generic_services():
    Scheduler.generic = Scheduler("scheduler")
    AsyncService.generic = AsyncService("async")
    NetworkService.generic = NetworkService("network")
    DownloadService.generic = DownloadService("download")
    ImageService.generic = ImageService("image")
    TaskService.generic = TaskService("task")
