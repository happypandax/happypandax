"""
Meta
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import arrow

from happypanda.common import constants, exceptions, utils, config
from happypanda.core.services import Service
from happypanda.core import command, message


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
        if not Service.get_command(x):
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
        cmd = Service.get_command(i)
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
        states[i] = Service.get_command(i).state.name

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
        cmd = Service.get_command(i)
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
        cmd = Service.get_command(i)
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
