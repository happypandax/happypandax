import logging
import pprint
import sys
import argparse
import traceback
import os

try:
    import rollbar  # updater doesn't need this
except ImportError:
    pass

from multiprocessing import Process, Queue, TimeoutError
from logging.handlers import RotatingFileHandler


from happypanda.common import constants


def shutdown(*args):
    logging.shutdown(*args)


def eprint(*args, **kwargs):
    "Prints to stderr"
    print(*args, file=sys.stderr, **kwargs)


class QueueHandler(logging.Handler):
    """
    This is a logging handler which sends events to a multiprocessing queue.
    """

    def __init__(self, queue):
        super().__init__()
        self.queue = queue

    def emit(self, record):
        try:
            ei = record.exc_info
            if ei:
                self.format(record)
                #dummy = self.format(record)
                record.exc_info = None
            self.queue.put_nowait(record)
        except (KeyboardInterrupt, SystemExit):
            raise
        except BaseException:
            self.handleError(record)


class Logger:

    report_online = False
    _queue = None

    def __init__(self, name):
        self.name = name
        self.category = ""
        if '.' in name:
            self.category = name.split('.')[0]
        self._logger = logging.getLogger(name)

    def exception(self, *args):
        ""
        self._log(self._logger.exception, *args, stderr=True)

    def i(self, *args, **kwargs):
        "INFO"
        self._log(self._logger.info, *args, **kwargs)

    def d(self, *args, **kwargs):
        "DEBUG"
        self._log(self._logger.debug, *args, **kwargs)

    def w(self, *args, **kwargs):
        "WARNING"
        self._log(self._logger.warning, *args, stderr=True, **kwargs)

    def e(self, *args, **kwargs):
        "ERROR"
        self._log(self._logger.error, *args, stderr=True, **kwargs)

    def c(self, *args, **kwargs):
        "CRITICAL"
        self._log(self._logger.critical, *args, stderr=True, **kwargs)

    def _log_format(self, *args):
        s = ""
        for a in args:
            if not isinstance(a, str):
                a = pprint.pformat(a)
            s += a
            s += " "
        return s

    def _log(self, level, *args, stdout=False, stderr=False):
        s = self._log_format(*args)
        level(s)
        if not constants.dev:
            if level in (self._logger.exception, self._logger.critical) and self.report_online:
                if constants.is_frozen:
                    if level == self._logger.exception:
                        rollbar.report_exc_info()
                    else:
                        rollbar.report_message(s, "critical")

        # prevent printing multiple times
        if not (constants.dev and not constants.is_frozen):
            def p(x):
                if stdout:
                    print(x)
                if stderr:
                    eprint(x)
            try:
                p(s)
            except OSError:  # raw write() returned invalid length 64 (should have been between 0 and 32)
                # fixed in python 3.6+
                s = s.encode("utf-8", errors="ignore").decode("ascii")
                p(s)

    def __getattr__(self, name):
        return getattr(self._logger, name)

    @classmethod
    def setup_logger(cls, args=None, logging_queue=None, main=False, debug=False):
        assert isinstance(args, argparse.Namespace) or args is None
        argsdev = getattr(args, 'dev', False)
        argsdebug = getattr(args, 'debug', False)

        if logging_queue:
            cls._queue = logging_queue
        log_level = logging.DEBUG if argsdebug else logging.INFO
        log_handlers = []
        if not argsdev:
            logging.raiseExceptions = False  # Don't raise exception if in production mode

        if cls._queue:
            lg = QueueHandler(cls._queue)
            if argsdebug:
                lg.setLevel(logging.DEBUG)
            log_handlers.append(lg)
        else:
            if argsdev:
                log_handlers.append(logging.StreamHandler())

            if argsdebug:
                try:
                    with open(constants.log_debug, 'x') as f:
                        pass
                except FileExistsError:
                    pass

                lg = logging.FileHandler(constants.log_debug, 'w', 'utf-8')
                lg.setLevel(logging.DEBUG)
                log_handlers.append(lg)

            for log_path, lvl in ((constants.log_normal, logging.INFO),
                                  (constants.log_error, logging.ERROR)):
                try:
                    with open(log_path, 'x') as f:  # noqa: F841
                        pass
                except FileExistsError:
                    pass
                lg = RotatingFileHandler(
                    log_path,
                    maxBytes=100000 * 10,
                    encoding='utf-8',
                    backupCount=1)
                lg.setLevel(lvl)
                log_handlers.append(lg)

        logging.basicConfig(
            level=log_level,
            format='%(asctime)-8s %(levelname)-10s %(name)-10s %(message)s',
            datefmt='%d-%m %H:%M',
            handlers=tuple(log_handlers))

        if main:
            if argsdev:
                Logger("sqlalchemy.pool").setLevel(logging.DEBUG)
                Logger("sqlalchemy.engine").setLevel(logging.INFO)
                Logger("sqlalchemy.orm").setLevel(logging.INFO)

            if debug:
                Logger(__name__).i(
                    os.path.split(
                        constants.log_debug)[1], "created at", os.path.abspath(
                        constants.log_debug), stdout=True)
            else:
                Logger("apscheduler").setLevel(logging.ERROR)

    @staticmethod
    def _listener(args, queue):
        Logger.setup_logger(args)
        while True:
            try:
                record = queue.get()
                if record is None:
                    break
                Logger(record.name).handle(record)
            except (KeyboardInterrupt, SystemExit):
                raise
            except BaseException:
                traceback.print_exc(file=sys.stderr)
        shutdown()
        queue.put(None)

    @classmethod
    def init_listener(cls, args):
        assert isinstance(args, argparse.Namespace)
        "Start a listener in a child process, returns queue"
        q = Queue()
        Process(target=Logger._listener, args=(args, q,), daemon=True).start()
        cls._queue = q
        return cls._queue

    @classmethod
    def shutdown_listener(cls):
        if cls._queue:
            cls._queue.put(None)
            try:
                cls._queue.get(timeout=3)
            except TimeoutError:
                pass
