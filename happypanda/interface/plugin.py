from happypanda.core import message


def get_plugin(plugin_id: str):
    """
    Get plugin information

    Args:
        plugin_id: get information for a specific plugin

    Returns:
        ```
        { plugin_id: }
        ```
    """
    return message.Message("works")

def install_plugin(plugin_id: str, ctx=None):
    """
    Install a plugin

    Args:
        plugin_id: UUID of plugin

    Returns:
        an error message object
    """
    return message.Message("works")


def uninstall_plugin(plugin_id: str, ctx=None):
    """
    Uninstall a plugin

    Args:
        plugin_id: UUID of plugin

    Returns:
        an error message object
    """
    return message.Message("works")


def list_plugins(ctx=None):
    """
    Get a list of available plugin information

    Args:
        an error message object
    """
    return message.Message("works")