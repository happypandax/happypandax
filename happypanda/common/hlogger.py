import logging
import pprint
import sys
import argparse
import traceback
import os

from multiprocessing import Process, Queue, TimeoutError
from logging.handlers import RotatingFileHandler


from happypanda.common import constants


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
        except:
            self.handleError(record)


class Logger:

    _queue = None

    def __init__(self, name):
        self.name = name
        self._logger = logging.getLogger(name)

    def exception(self, *args):
        ""
        self._log(self._logger.exception, *args, stderr=True)

    def i(self, *args, **kwargs):
        "INFO"
        self._log(self._logger.info, *args, **kwargs)

    def d(self, *args, **kwargs):
        "INFO"
        self._log(self._logger.debug, *args, **kwargs)

    def w(self, *args, **kwargs):
        "INFO"
        self._log(self._logger.warning, *args, stderr=True, **kwargs)

    def e(self, *args, **kwargs):
        "INFO"
        self._log(self._logger.error, *args, stderr=True, **kwargs)

    def c(self, *args, **kwargs):
        "INFO"
        self._log(self._logger.critical, *args, stderr=True, **kwargs)

    def _log(self, level, *args, stdout=False, stderr=False):
        s = ""
        for a in args:
            if not isinstance(a, str):
                a = pprint.pformat(a)
            s += a
            s += " "
        level(s)

        if not constants.dev:  # prevent printing multiple times
            if stdout:
                print(s)
            if stderr:
                eprint(s)

    def __getattr__(self, name):

        if not hasattr(self._logger, name):
            raise AttributeError
        return getattr(self._logger, name)

    @classmethod
    def setup_logger(cls, args, logging_queue=None, main=False):
        assert isinstance(args, argparse.Namespace)
        if logging_queue:
            cls._queue = logging_queue
        log_level = logging.DEBUG if args.debug else logging.INFO
        log_handlers = []
        if not args.dev:
            logging.raiseExceptions = False  # Don't raise exception if in production mode

        if cls._queue:
            log_handlers.append(QueueHandler(cls._queue))
        else:
            if args.dev:
                log_handlers.append(logging.StreamHandler())

            if args.debug:
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
            Logger(__name__).i(
                os.path.split(
                    constants.log_debug)[1], "created at", os.path.abspath(
                    constants.log_debug), stdout=True)

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
            except:
                traceback.print_exc(file=sys.stderr)
        queue.put(None)

    @classmethod
    def init_listener(cls, args):
        assert isinstance(args, argparse.Namespace)
        "Start a listener in a child process, returns queue"
        cls._queue = Queue()
        Process(target=Logger._listener, args=(args, cls._queue,), daemon=True).start()
        return cls._queue

    @classmethod
    def shutdown_listener(cls):
        if cls._queue:
            cls._queue.put(None)
            try:
                cls._queue.get(timeout=3)
            except TimeoutError:
                pass
