"""
Meta
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import arrow
import os
import yaml

from happypanda.common import constants, exceptions, utils, config, hlogger
from happypanda.core.services import AsyncService
from happypanda.core import command, message
from happypanda.core.commands import meta_cmd
from happypanda.interface import enums

log = hlogger.Logger(__name__)


def get_changelog():
    """
    Get the changelog in markdown formatted text
    The changelog returned is for the current release or a new update

    Returns:

        .. code-block:: guess

            {
                'version': str,
                'changes': str
            }

    .. seealso::

        :func:`.check_update`

    """

    ch = {'version': '', 'changes': ''}
    lr = constants.internaldb.latest_release.get(None)
    if lr:
        ch['changes'] = lr.get("changes", "")
        ch['version'] = lr.get("tag", "")

    return message.Identity("changelog", ch)


def get_locales():
    """
    Retrieve available translation locales

    Returns:

        .. code-block:: guess

            {
                str : {
                            'locale' : str
                            'namespaces': [str, ...]
                        }
            }

    .. seealso::

        :func:`.translate`
    """

    if constants.translations is None:
        trs_dict = {}
        for f in os.scandir(constants.dir_translations):
            if not f.is_file or not f.name.endswith(".yaml"):
                continue
            n = f.name.split(".")
            if len(n) == 3:
                t_locale, t_ns, _ = n
                l_dict = trs_dict.setdefault(t_locale, {})
                if 'locale' not in l_dict:
                    t_general = "{}.general.yaml".format(t_locale)
                    t_general_path = os.path.join(constants.dir_translations, t_general)
                    if not os.path.exists(t_general_path):
                        continue
                    try:
                        with open(t_general_path, "r", encoding="utf-8") as rf:
                            f_dict = yaml.safe_load(rf)
                            if 'locale' in f_dict:
                                l_dict['locale'] = f_dict['locale']
                    except yaml.YAMLError as e:
                        log.w("Failed to load translation file {}:".format(t_general), e)
                        continue

                l_dict.setdefault('namespaces', []).append(t_ns)
        constants.translations = trs_dict

    d = {}
    for a, b in constants.translations.items():
        if 'locale' not in b:
            continue
        d[a] = b

    return message.Identity("locales", d)


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

        .. code-block:: guess

            {
                'url' : str,
                'tag' : str
                'changes' : str,
            }

        or ``null``

    |async command|

    .. seealso::

        :func:`.get_changelog` -- when a new update is found, its changelog is immediately available here

    """

    upd = meta_cmd.CheckUpdate(AsyncService.generic).run(force=True, push=push)
    return message.Identity('update', upd)


def update_application(download_url: str = None, restart: bool = True):
    """
    Update the application with a new release.
    If download_url is not provided, a check for a new release will occur

    Args:
        download_url: a url to the release file, can be path to file on the system
        restart: restart the application after installing the new update


    Returns:
        A ``bool`` indicating whether the install was successful or not

    |async command|
    """

    upd = meta_cmd.UpdateApplication(AsyncService.generic).run(download_url, restart)
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
    if ids is None:
        return
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
        if cmd.state not in (enums.CommandState.finished, enums.CommandState.stopped):
            if cmd.state == enums.CommandState.failed:
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
                command_id : :py:class:`.CommandState`
            }
    """

    _command_msg(command_ids)

    states = {}

    for i in command_ids:
        states[i] = AsyncService.get_command(i).state.name

    return message.Identity('command_state', states)


def get_command_progress(command_ids: list = None):
    """
    Get progress of command operation

    If the command did not set a maximum value, the returned percent will be set to less than ``0.0`` for infinity.

    This should be polled every few seconds to get updated values.

    Args:
        command_ids: list of command ids or None to retrieve progress of all occurring commands

    Returns:
        .. code-block:: guess

            {
                command_id : {  'title': str,
                                'value': float,
                                'subtitle': str,
                                'subtype': :py:class:`.ProgressType`,
                                'max': float,
                                'percent': float,
                                'type': :py:class:`.ProgressType`,
                                'text': str,
                                'timestamp':int,
                                'state': :py:class:`.CommandState`
                                }
            }

        or

        .. code-block:: guess

            {
                command_id : None
            }

        or, if ``command_ids`` is ``None``:

        .. code-block:: guess

            [
                {   'title': str,
                    'value': float,
                    'subtitle': str,
                    'subtype': :py:class:`.ProgressType`,
                    'max': float,
                    'percent': float,
                    'type': :py:class:`.ProgressType`,
                    'text': str,
                    'timestamp':int
                    },
                ...
            ]
    """
    _command_msg(command_ids)

    cmd_p = []
    if command_ids is not None:
        for i in command_ids:
            cmd = AsyncService.get_command(i)
            if cmd:
                cmd_p.append((i, cmd.get_progress()))
    else:
        cmd_p = command.CoreCommand.get_all_progress()

    progs = {} if command_ids is not None else []

    for x in cmd_p:
        p = x[1] if command_ids is not None else x
        for k in ('type', 'subtype'):
            if p and not p[k]:
                p[k] = enums.ProgressType.Unknown
            if p and p[k]:
                p[k] = p[k].value

        if command_ids is not None:
            progs[x[0]] = p
        else:
            progs.append(p)

    return message.Identity('command_progress', progs)


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
