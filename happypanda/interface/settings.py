"""
Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Most configuration keys can be stored and retrieved by ``namespace.key``

See :ref:`Settings` for all server defined configuration keys and their default values.

There exists the special namespace ``this`` to retrieve and store configuration only visible to the
client in question. The server will resolve the namespace ``this`` to the :ref:`session <Session>` owner's name
(the client that created the session).
These configuration keys will appear in the server's ``config.yaml`` file upon save.

"""

from happypanda.common import utils, exceptions, config
from happypanda.core import message


def _get_cfg(keyname, can_raise=True):

    try:
        ns, key = [x.strip() for x in keyname.strip().split('.') if x]
    except ValueError:
        raise exceptions.APIError(
            utils.this_function(),
            "Invalid setting '{}'".format(keyname))

    cfg = config.config
    ctx = utils.get_context()
    client_space = False
    if ns.lower() == 'this':
        client_space = True
        ns = ctx['name']
        if ns.lower in config.ConfigNode.default_namespaces:
            raise exceptions.APIError(
                utils.this_function(),
                "Client name '{}' coincides with default namespace '{}'. Please use a different client name".format(ns, ns.lower()))

    with cfg.tmp_config(ns, ctx['config']):
        if not cfg.key_exists(ns, key):
            if not client_space or (client_space and can_raise):
                raise exceptions.SettingsError(utils.this_function(),
                                               "Setting with key '{}' does not exist".format(keyname))
    return ns, key


def set_config(cfg: dict):
    """
    Set/update configuration

    Args:
        cfg: a dict containing ``namespace.key``:``value``

    Returns:
        Status
    """
    client_cfg = utils.get_context()['config']
    for set_key in cfg:
        ns, key = _get_cfg(set_key, False)
        default_ns = ns.lower() in config.ConfigNode.default_namespaces
        if default_ns:
            if config.ConfigNode.get_isolation_level(ns, key) == config.ConfigIsolation.client:
                client_cfg.setdefault(config.config.format_namespace(ns), {})[key.lower()] = cfg[set_key]
                continue

        with config.config.namespace(ns):
            config.config.update(key, cfg[set_key], create=not default_ns)

    return message.Message("updated")


def get_config(cfg: dict = {}):
    """
    Get configuration

    Args:
        cfg: a dict containing ``namespace.key``:``default value`` or an empty dict to retrieve all settings

    Returns:
        .. code-block:: guess

            {
                'namespace.key': value
            }

    """

    values = {}

    if cfg:
        for set_key in cfg:
            ns, key = _get_cfg(set_key, cfg[set_key] is None)

            with config.config.tmp_config(ns, utils.get_context()['config']):
                values[set_key] = config.config.get(ns, key, cfg[set_key])
    else:
        with config.config.tmp_config(None, utils.get_context()['config']):
            s = config.config.get_all()
            for ns in s:
                if ns in config.ConfigNode.default_namespaces:
                    values[ns] = s[ns]
                elif ns == utils.get_context()['name'].lower():
                    values["this"] = s[ns]
    return message.Identity('config', values)


def save_config():
    """
    Save config to disk

    Returns:
        Status
    """
    config.config.save()
    return message.Message("saved")
