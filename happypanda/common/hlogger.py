import logging
import pprint
import sys

from happypanda.common import constants

def eprint(*args, **kwargs):
    "Prints to stderr"
    print(*args, file=sys.stderr, **kwargs)

class Logger:

    def __init__(self, name):
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
