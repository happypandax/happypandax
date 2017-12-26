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

class UpdateApplication(Command):
    """
    Check for new release and update the application
    """

    update = CommandEvent("update", bool, bool)

    def __init__(self, priority = constants.Priority.Low):
        super().__init__(priority)

    def main(self, download_url=None, restart=True, silent=True) -> bool:
        st = False
        if download_url:
            rel = download_url
        else:
            rel = updater.check_release(silent=silent)
            if rel:
                rel = rel['url']
        if rel:
            new_rel = updater.get_release(rel, silent=silent)
            if new_rel:
                st = updater.register_release(new_rel['path'], silent, restart=restart)
        self.update.emit(st, restart)
        return st

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