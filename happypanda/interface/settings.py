from happypanda.common import constants, utils, exceptions
from happypanda.core import message


def _get_cfg(keyname, ctx):

    try:
        ns, key = [x.strip() for x in keyname.strip().split('.') if x]
    except ValueError:
        raise exceptions.APIError(
            utils.this_function(),
            "Invalid setting keyname: '{}'".format(keyname))

    cfg = constants.config

    if ns.lower() == 'this':
        pass

    if not cfg.key_exists(ns, key):
        raise exceptions.SettingsError(utils.this_function(), "Setting doesn't exist: '{}'".format(keyname))

    return ns, key, cfg


def set_settings(settings: dict = {}, ctx=None):
    """
    Set settings

    Args:
        settings: a dict containing ``key.name``:``value``

    Returns:
        Status
    """

    return message.Message("ok")


def get_settings(settings: dict = {}, ctx=None):
    """
    Get settings

    Args:
        settings: a dict containing ``key.name``:``default value``, send an empty dict to retrieve all settings

    Returns:
        ```
        { 'key.name': value }
        ```
    """
    utils.require_context(ctx)

    values = {}

    if settings:
        for set_key in settings:
            ns, key, cfg = _get_cfg(set_key, ctx)

            values[set_key] = cfg.get(ns, key, settings[set_key])
    else:
        raise NotImplementedError
    return message.Identity('settings', values)
