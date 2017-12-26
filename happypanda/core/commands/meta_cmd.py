from happypanda.common import (hlogger, exceptions, utils, constants, exceptions, config)
from happypanda.core.command import Command, CommandEvent, AsyncCommand
from happypanda.interface import enums
from happypanda.core import updater

log = hlogger.Logger(__name__)

class CheckUpdate(Command):
    """
    Check for new release
    """

    def __init__(self, priority = constants.Priority.Low):
        super().__init__(priority)

    def main(self, silent=True) -> dict:
        return updater.check_release(silent=silent)

class CheckUpdate(Command):
    """
    Check for new release and update
    """

    def __init__(self, priority = constants.Priority.Low):
        super().__init__(priority)

    def main(self, silent=True) -> dict:
        return updater.check_release(silent=silent)
    
class RestartApplication(Command):
    """
    Restart the appplication
    """

    restart = CommandEvent("restart")

    def __init__(self, priority = constants.Priority.Normal):
        super().__init__(priority)

    def main(self):
        self.restart.emit()

class ShutdownApplication(Command):
    """
    Shutdown the appplication
    """

    shutdown = CommandEvent("shutdown")

    def __init__(self, priority = constants.Priority.Normal):
        super().__init__(priority)

    def main(self):
        self.shutdown.emit()