"""
About config...

.. todo::
    explain ``this`` namespace
"""

from happypanda.common import constants, utils, exceptions, config
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
                raise exceptions.SettingsError(utils.this_function(), "Setting with key '{}' does not exist".format(keyname))
    return ns, key


def set_config(cfg: dict = {}):
    """
    Set/update configuration

    Args:
        cfg: a dict containing ``namespace.key``:``value``

    Returns:
        Status
    """

    for set_key in cfg:
        ns, key = _get_cfg(set_key, False)

        #if self.isolation == ConfigIsolation.client:
        #    with self._cfg.tmp_config(self.namespace, self._get_ctx_config().get(self._cfg._get_namespace(self.namespace))):
        #        self._cfg.update(self.name, new_value)
        #else:
        #    with self._cfg.namespace(self.namespace):
        #        self._cfg.update(self.name, new_value)

    return message.Message("updated")


def get_config(cfg: dict = {}):
    """
    Get configuration

    Args:
        cfg: a dict containing ``namespace.key``:``default value``, send an empty dict to retrieve all settings

    Returns:
        ```
        { 'key.name': value }
        ```
    """

    values = {}

    if cfg:
        for set_key in cfg:
            ns, key = _get_cfg(set_key)

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
