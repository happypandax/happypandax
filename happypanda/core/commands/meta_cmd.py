"""
Meta CMD
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import typing

from happypanda.common import (hlogger, constants, config)
from happypanda.core.command import Command, CommandEvent, AsyncCommand, CParam
from happypanda.core import updater, message
from happypanda.interface import enums

log = hlogger.Logger(constants.log_ns_command + __name__)


class CheckUpdate(AsyncCommand):
    """
    Check for new release

    Args:
        silent: supress all errors
        force: bypass user config on allowing checking for updates
        push: push notifications on found update

    Returns:
        .. code-block:: guess

            {
            'url':'',
            'changes':'',
            'tag':'',
            'version':(0, 0, 0)
            }
        
        when there is a new release, or ``None``
    """

    def __init__(self, service=None, priority=constants.Priority.Low):
        return super().__init__(service, priority)

    def main(self, silent: bool=True, force: bool=False, push: bool=False) -> typing.Union[dict, None]:
        if force or config.check_release_interval.value:
            self.set_progress(type_=enums.ProgressType.CheckUpdate)
            self.set_max_progress(2)
            u = updater.check_release(silent=silent, cmd=self)
            self.set_progress(1)
            if u:
                init_update = True
                init_restart = True
                if push:
                    if config.auto_install_release.value:
                        msg = message.Notification(
                            "Downloading and installing new update...",
                            "A new update {} is available!".format(u['tag']))
                        msg.id = constants.PushID.Update.value
                        self.push(msg)
                    else:
                        msg = message.Notification(
                            "A new update is available!",
                            "HappyPanda X {} is available!".format(u['tag']))
                        msg.id = constants.PushID.Update.value
                        msg.add_action(1, "Update & Restart", "button")
                        msg.add_action(2, "Update", "button")
                        msg.add_action(3, "Skip", "button")
                        client_answer = self.push(msg).get(msg.id, timeout=constants.notif_long_timeout)
                        if not client_answer or 3 in client_answer:
                            init_update = False
                        if client_answer and 2 in client_answer:
                            init_restart = False
                if init_update:
                    upd = UpdateApplication()
                    upd.merge_progress_into(self)
                    upd.main(u['url'], restart=init_restart, silent=silent, push=push)
            self.set_progress(2)
            return u


class UpdateApplication(AsyncCommand):
    """
    Check for new release and update the application

    Args:
        download_url: url to file which is to be downloaded, if ``None`` the url will be retrieved with :func:`CheckUpdate`
        restart: call :func:`RestartApplication` when the update has been registered
        silent: supress all errors
        push: push notifications on update

    Returns:
        bool indicating whether the update has been registered or not
    """

    update = CommandEvent("update",
                          CParam("status", bool, "whether the update has been registered or not"),
                          CParam("restart", bool, "whether the call :func:`RestartApplication` if the update was registered"),
                          __doc="""
                          Emitted at the end of the process
                          """
                          )

    def __init__(self, service=None, priority=constants.Priority.Low):
        return super().__init__(service, priority)

    def main(self, download_url: str=None, restart: bool=True, silent: bool=True, push: bool=False) -> bool:
        self.set_progress(type_=enums.ProgressType.UpdateApplication)
        self.set_max_progress(3)
        st = False
        if download_url:
            rel = download_url
        else:
            rel = updater.check_release(silent=silent, cmd=self)
            if rel:
                rel = rel['url']
        self.set_progress(1)
        if rel:
            new_rel = updater.get_release(rel, silent=silent, cmd=self)
            self.set_progress(2)
            if new_rel:
                st = updater.register_release(new_rel['path'], silent, restart=restart)
                self.set_progress(3)
                if push:
                    if restart:
                        m = "Restarting and installing new update..."
                    else:
                        m = "The update will be installed on the next startup"
                    msg = message.Notification(
                        m,
                        "A new update is pending to be installed")
                    msg.id = constants.PushID.Update.value
                    self.push(msg)
        self.update.emit(st, restart)
        return st


class RestartApplication(Command):
    """
    Restart the appplication
    """

    restart = CommandEvent("restart",
                           __doc="""
                           Emitted when about to restart
                           """)

    def __init__(self, priority=constants.Priority.Normal):
        super().__init__(priority)

    def main(self):
        self.restart.emit()


class ShutdownApplication(Command):
    """
    Shutdown the appplication
    """

    shutdown = CommandEvent("shutdown",
                            __doc="""
                            Emitted when about to shutdown
                            """)

    def __init__(self, priority=constants.Priority.Normal):
        super().__init__(priority)

    def main(self):
        self.shutdown.emit()


class InitApplication(Command):
    """
    Initialize the appplication
    """

    init = CommandEvent("init",
                        __doc="""
                        Emitted on application startup where everything has been initialized after the server has started.
                        """)

    def __init__(self, priority=constants.Priority.Normal):
        super().__init__(priority)

    def main(self):
        self.init.emit()
