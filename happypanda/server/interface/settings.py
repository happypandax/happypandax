from happypanda.common import constants, message, utils, exceptions


def set_settings(settings={}, ctx=None):
    """
    Set settings

    Params:
        - settings -- a dictionary containing key:value pairs

    Returns:
        Status
    """

    return message.Message("ok")


def get_settings(settings=[], ctx=None):
    """
    Set settings
    Send empty list to get all key:values

    Params:
        - set_list -- a list of setting keys

    Returns:
        dict of key.name:value
    """
    utils.require_context(ctx)

    values = {}

    if settings:
        for set_key in settings:
            try:
                ns, key = [x.strip() for x in set_key.strip().split('.') if x]
            except ValueError:
                raise exceptions.APIError(
                    utils.this_function(),
                    "Invalid setting: '{}'".format(set_key))

            if constants.config.key_exists(ns, key):
                values[set_key] = constants.config.get(ns, key)
            elif ns.lower() == 'self' and ctx.config and ctx.config.key_exists(ns, key):
                values[set_key] = ctx.config.get(ns, key)
                raise NotImplementedError
            else:
                raise exceptions.APIError(
                    utils.this_function(),
                    "Setting doesn't exist: '{}'".format(set_key))
    else:
        raise NotImplementedError
    return message.Identity('settings', values)
