"""
Plugin
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
from happypanda.common import constants
from happypanda.interface import enums
from happypanda.core import plugins, message

def list_plugins(state: enums.PluginState=None):
    """
    Get a list plugins

    Args:
        state: filter list by plugin state

    Returns:
        .. code-block:: guess

            {
            }
    """
    l = message.List('plugins', message.Plugin)
    for n in constants.plugin_manager._nodes:
        l.append(message.Plugin(n))
    return l

def get_plugin(plugin_id: str):
    """
    Get information for a specific plugin

    Args:
        plugin_id: UUID4 of plugin

    Returns:
        .. code-block:: guess

            {
            }
    """
    return message.Plugin(constants.plugin_manager.get_node(plugin_id))


def install_plugin(plugin_id: str):
    """
    Install a plugin

    Args:
        plugin_id: UUID4 of plugin

    Returns:
        status
    """
    constants.plugin_manager.install_plugin(plugin_id)

def disable_plugin(plugin_id: str):
    """
    Disable a plugin

    Args:
        plugin_id: UUID4 of plugin

    Returns:
        status
    """
    constants.plugin_manager.disable_plugin(plugin_id)

