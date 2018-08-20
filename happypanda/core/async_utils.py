import sys
import gevent
import weakref
import collections
import arrow
import psycopg2
import functools

from psycopg2 import extensions
from gevent.socket import wait_read, wait_write
from gevent import monkey

from happypanda.common import hlogger, utils, constants
from happypanda.core import db

log = hlogger.Logger(constants.log_ns_core + __name__)
Thread = monkey.get_original("threading", "Thread")
local = monkey.get_original("threading", "local")


class Greenlet(gevent.Greenlet):
    '''
    A subclass of gevent.Greenlet which adds additional members:
     - locals: a dict of variables that are local to the "spawn tree" of
       greenlets
     - spawner: a weak-reference back to the spawner of the
       greenlet
     - stacks: a record of the stack at which the greenlet was
       spawned, and ancestors
    '''

    def __init__(self, f, *a, **kw):
        super().__init__(f, *a, **kw)
        self._hp_inherit(self, weakref.proxy(gevent.getcurrent()), sys._getframe())

    @staticmethod
    def _hp_inherit(self, parent, frame):
        self.spawn_parent = parent
        self.locals = getattr(self.spawn_parent, "locals", {})
        stack = []
        cur = frame
        while cur:
            stack.extend((cur.f_code, cur.f_lineno))
            cur = cur.f_back
        self.stacks = (tuple(stack),) + getattr(parent, 'stacks', ())[:10]

    @staticmethod
    def _reset_locals(greenlet):
        if hasattr(greenlet, 'locals'):
            greenlet.locals = {}


def _daemon():
    while True:
        gevent.sleep(0.1)


class CPUThread():
    """
    Manages a single worker thread to dispatch cpu intensive tasks to.
    Signficantly less overhead than gevent.threadpool.ThreadPool() since it
    uses prompt notifications rather than polling.  The trade-off is that only
    one thread can be managed this way.
    Since there is only one thread, hub.loop.async() objects may be used
    instead of polling to handle inter-thread communication.
    """

    _threads = []

    def __init__(self, name=""):
        self.name = name
        self.in_q = collections.deque()
        self.out_q = collections.deque()
        self.in_async = None
        self.out_async = gevent.get_hub().loop.async()
        self.out_q_has_data = gevent.event.Event()
        self.out_async.start(self.out_q_has_data.set)
        self.worker = Thread(target=self._run)
        self.worker.daemon = True
        self.stopping = False
        self.results = {}
        # start running thread / greenlet after everything else is set up
        self.worker.start()
        self.notifier = gevent.spawn(self._notify)
        self.worker_count = 0
        self.last_worker_start = arrow.now()

    def _run(self):
        # in_cpubound_thread is sentinel to prevent double thread dispatch
        thread_ctx = local()
        thread_ctx.in_cpubound_thread = True
        daemon_gevent = None
        try:
            self.in_async = gevent.get_hub().loop.async()

            daemon_gevent = gevent.spawn(_daemon)
            self.in_q_has_data = gevent.event.Event()
            self.in_async.start(self.in_q_has_data.set)
            while not self.stopping:
                if not self.in_q:
                    # wait for more work
                    self.in_q_has_data.clear()
                    self.in_q_has_data.wait()
                    continue
                # arbitrary non-preemptive service discipline can go here
                # FIFO for now
                jobid, func, args, kwargs = self.in_q.popleft()
                start_time = arrow.now()
                log.d(f"Running function in {self.name}: {func}")
                try:
                    with db.cleanup_session():
                        self.results[jobid] = func(*args, **kwargs)
                except Exception as e:
                    log.exception(f"Exception raised in {self.name}:")
                    self.results[jobid] = self._Caught(e)
                finished_time = arrow.now()
                run_delta = finished_time - start_time
                log.d("Function - '{}'\n".format(func.__name__),
                      "\tRunning time: {}\n".format(run_delta),
                      "\tJobs left:", len(self.in_q),
                      )
                self.out_q.append(jobid)
                self.out_async.send()
        except BaseException:
            self._error()
            # this may always halt the server process
        if daemon_gevent:
            daemon_gevent.kill()

    def apply(self, func, args, kwargs):
        done = gevent.event.Event()
        self.in_q.append((done, func, args, kwargs))
        while not self.in_async:
            gevent.sleep(0.01)  # poll until worker thread has initialized
        self.in_async.send()
        self.worker_count += 1
        self.last_worker_start = arrow.now()
        done.wait()
        self.worker_count -= 1
        res = self.results[done]
        del self.results[done]
        if isinstance(res, self._Caught):
            raise res.err
        return res

    def _notify(self):
        try:
            while not self.stopping:
                if not self.out_q:
                    # wait for jobs to complete
                    self.out_q_has_data.clear()
                    self.out_q_has_data.wait()
                    continue
                self.out_q.popleft().set()
        except BaseException:
            self._error()

    class _Caught(object):
        def __init__(self, err):
            self.err = err

    def __repr__(self):
        cn = self.__class__.__name__
        return ("<%s@%s in_q:%s out_q:%s>" %
                (cn, id(self), len(self.in_q), len(self.out_q)))

    def _error(self):
        # TODO: something better, but this is darn useful for debugging
        log.exception()


class AsyncFuture:

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
        if self._future:
            self._future.kill()


def defer(f=None, predicate=None):
    """
    Schedule a function to run in a cpu_bound thread, returns a AsyncFuture
    Optional predicate parameter to determine if the function should be dispatched
    """
    if f is None:
        def p_wrap(f):
            return defer(f, predicate)
        return p_wrap
    else:
        def f_wrap(f, *args, **kwargs):
            if not CPUThread._threads:
                for x in range(constants.maximum_cpu_threads):
                    CPUThread._threads.append(CPUThread(f"cpu thread {x}"))
            cpu_threads_by_count = sorted(CPUThread._threads,
                                          key=lambda c: c.worker_count) if CPUThread._threads else []
            cpu_threads_by_time = sorted(cpu_threads_by_count, reverse=True, key=lambda c: c.last_worker_start)
            if cpu_threads_by_count and cpu_threads_by_time:
                cpu_thread = cpu_threads_by_count[0]
                if cpu_thread.worker_count:
                    cpu_thread = cpu_threads_by_time[0]

                log.d(f"Putting function in {cpu_thread.name}: {f}")
                r = cpu_thread.apply(f, args, kwargs)
            else:
                r = f(*args, **kwargs)
            return r

        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            a = AsyncFuture(None, None)
            # TODO: unit test this
            if (predicate is not None and not predicate) or utils.in_cpubound_thread():
                v = f(*args, **kwargs)
                a._value = v
            else:
                g = Greenlet(f_wrap, f, *args, **kwargs)
                g.start()
                a._future = g
            return a
        return wrapper


def patch_psycopg():
    """
    Configure Psycopg to be used with gevent in non-blocking way.
    """
    if not hasattr(extensions, 'set_wait_callback'):
        raise ImportError(
            "support for coroutines not available in this Psycopg version ({})".format(psycopg2.__version__))

    extensions.set_wait_callback(gevent_wait_callback)


def gevent_wait_callback(conn, timeout=None):
    """
    A wait callback useful to allow gevent to work with Psycopg.
    """
    while True:
        state = conn.poll()
        try:
            if state == extensions.POLL_OK:
                break
            elif state == extensions.POLL_READ:
                wait_read(conn.fileno(), timeout=timeout)
            elif state == extensions.POLL_WRITE:
                wait_write(conn.fileno(), timeout=timeout)
            else:
                raise psycopg2.OperationalError(
                    "Bad result from poll: {}".format(state))
        except gevent.GreenletExit:  # greenlet timed-out, probably a very bad solution
            log.e("Psycopg wait callback timed-out", timeout, "state:", state)
