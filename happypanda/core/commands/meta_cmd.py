from happypanda.common import (hlogger, constants, config)
from happypanda.core.command import Command, CommandEvent, AsyncCommand
from happypanda.core import updater, message
from happypanda.interface import enums

log = hlogger.Logger(__name__)


class CheckUpdate(AsyncCommand):
    """
    Check for new release
    """

    def __init__(self, service = None, priority = constants.Priority.Low):
        return super().__init__(service, priority)

    def main(self, silent=True, force=False, push=False) -> dict:
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
                            "Downloading and installing...\nChangelog coming soon! For now, please visit the github repo to see the new changes",
                            "A new update {} is available!".format(u['tag']))
                        msg.id = constants.PushID.Update.value
                        self.push(msg)
                    else:
                        msg = message.Notification(
                            "Changelog coming soon! For now, please visit the github repo to see the new changes",
                            "HappyPanda X {} is available!".format(u['tag']))
                        msg.id = constants.PushID.Update.value
                        msg.add_action(1, "Update & Restart", "button")
                        msg.add_action(2, "Update", "button")
                        msg.add_action(3, "Skip", "button")
                        client_answer = self.push(msg).get(msg.id, timeout=30)
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
    """

    update = CommandEvent("update", bool, bool)

    def __init__(self, service = None, priority = constants.Priority.Low):
        return super().__init__(service, priority)

    def main(self, download_url=None, restart=True, silent=True, push=False) -> bool:
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

    restart = CommandEvent("restart")

    def __init__(self, priority=constants.Priority.Normal):
        super().__init__(priority)

    def main(self):
        self.restart.emit()


class ShutdownApplication(Command):
    """
    Shutdown the appplication
    """

    shutdown = CommandEvent("shutdown")

    def __init__(self, priority=constants.Priority.Normal):
        super().__init__(priority)

    def main(self):
        self.shutdown.emit()
