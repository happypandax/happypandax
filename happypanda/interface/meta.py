"""
Meta
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import arrow

from happypanda.common import constants, exceptions, utils, config, hlogger
from happypanda.core.services import AsyncService
from happypanda.core import command, message
from happypanda.core.commands import meta_cmd

log = hlogger.Logger(__name__)


# def get_error(code: int, id: int):
#    """
#    Get error

#    Args:
#        code: error code, refer to ...
#        id:

#    Returns:
#        an error message object
#    """
#    return message.Message("works")

def get_notification(scope=None, msg_id: int=None, expired: bool = False):
    """
    Not ready yet...
    """
    msg = None
    if constants.notification:
        msg = constants.notification._fetch(scope=scope, expired=expired)

    return msg if msg else message.Identity("notification", msg)


def reply_notification(msg_id: int, action_values: dict):
    """
    Not ready yet...
    """
    s = False
    if constants.notification:
        constants.notification.reply(msg_id, action_values)
        s = True
    return message.Identity("status", s)


def check_update(push: bool = False):
    """
    Check for new release

    Args:
        push: whether to push out notifications if an update is found

    Returns:
        an empty dict or

        .. code-block:: guess

            {
                'url' : str,
                'tag' : str
                'changes' : str,
            }
    """

    r = {}
    upd = meta_cmd.CheckUpdate().run(force=True, push=push)
    if upd:
        r = upd
    return message.Identity('update', r)


def update_application(download_url: str = None, restart: bool = True):
    """
    Update the application with a new release.
    If download_url is not provided, a check for a new release will occur

    Args:
        download_url: a url to the release file, can be path to file on the system
        restart: restart the application after installing the new update

    Returns:
        bool indicating whether the install was successful or not
    """

    upd = meta_cmd.UpdateApplication().run(download_url, restart)
    return message.Identity('update', upd)


def restart_application():
    """
    Restart the application

    Returns:
        This function will not return
    """
    meta_cmd.RestartApplication().run()
    return message.Identity('status', True)


def shutdown_application():
    """
    Shutdown the application

    Returns:
        This function will not return
    """
    meta_cmd.ShutdownApplication().run()
    return message.Identity('status', True)


def get_version():
    """
    Get version of components: 'core', 'db' and 'torrent'

    Returns:
        .. code-block:: guess

            {
                'core' : [int, int, int],
                'db' : [int, int, int],
                'torrent' : [int, int, int],
            }
    """
    vs = dict(
        core=list(constants.version),
        db=list(constants.version_db),
        torrent=(0, 0, 0)
    )
    return message.Identity("version", vs)


def _command_msg(ids):
    for x in ids:
        c = AsyncService.get_command(x)
        if not c:
            raise exceptions.CommandError(utils.this_function(), "Command with ID '{}' does not exist".format(x))


def get_command_value(command_ids: list):
    """
    Get the returned command value

    Args:
        command_ids: list of command ids

    Returns:
        .. code-block:: guess

            {
                command_id : value
            }
    """

    _command_msg(command_ids)

    values = {}

    for i in command_ids:
        cmd = AsyncService.get_command(i)
        if cmd.state not in (command.CommandState.finished, command.CommandState.stopped):
            if cmd.state == command.CommandState.failed:
                raise exceptions.CommandError(utils.this_function(), "Command with ID '{}' has failed".format(i))
            raise exceptions.CommandError(utils.this_function(),
                                          "Command with ID '{}' has not finished running".format(i))

        if isinstance(cmd.value, message.CoreMessage):
            values[i] = cmd.value.json_friendly(include_key=False)
        else:
            values[i] = cmd.value
        if config.debug.value:
            cmd._log_stats(arrow.now())

    return message.Identity('command_value', values)


def get_command_state(command_ids: list):
    """
    Get state of command

    Args:
        command_ids: list of command ids

    Returns:
        .. code-block:: guess

            {
                command_id : state
            }
    """

    _command_msg(command_ids)

    states = {}

    for i in command_ids:
        states[i] = AsyncService.get_command(i).state.name

    return message.Identity('command_state', states)


# def get_command_progress(command_ids: list):
#    """
#    Get progress of command in percent

#    Args:
#        command_ids: list of command ids

#    Returns:
#        .. code-block:: guess

#            {
#                command_id : progress
#            }
#    """
#    return message.Message("works")


def stop_command(command_ids: list):
    """
    Stop command from running

    Args:
        command_ids: list of command ids

    Returns:
        .. code-block:: guess

            {
                command_id : state
            }
    """
    _command_msg(command_ids)

    states = {}

    for i in command_ids:
        cmd = AsyncService.get_command(i)
        cmd.stop()
        states[i] = cmd.state.name

    return message.Identity('command_state', states)


def start_command(command_ids: list):
    """
    Start running a command

    Args:
        command_ids: list of command ids

    Returns:
        .. code-block:: guess

            {
                command_id : state
            }
    """
    _command_msg(command_ids)

    states = {}

    for i in command_ids:
        cmd = AsyncService.get_command(i)
        cmd.start()
        states[i] = cmd.state.name

    return message.Identity('command_state', states)


# def get_command_error(command_ids: list):
#    """
#    Get error raised during command runtime

#    Args:
#        command_ids: list of command ids

#    Returns:
#        .. code-block:: guess

#            {
#                command_id : error
#            }
#    """
#    return message.Message("works")


# def undo_command(command_ids: list):
#    """
#    Undo a command

#    Args:
#        command_ids: list of command ids

#    Returns:
#        .. code-block:: guess

#            {
#                command_id : state
#            }

#    .. Note::
#        Only select commands are undoable
#    """
#    return message.Message("works")
