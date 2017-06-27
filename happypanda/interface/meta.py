from happypanda.common import constants, message


def get_error(code: int, id: int, ctx=None):
    """
    Get error

    Args:
        code: error code, refer to ...
        id:

    Returns:
        an error message object
    """
    return message.Message("works")


def get_version():
    """
    Get version of components: 'core', 'db' and 'torrent'

    Returns:
        a dict of component: list of major, minor, patch
    """
    vs = dict(
        core=list(constants.version),
        db=list(constants.version_db),
        torrent=(0, 0, 0)
    )
    return message.Identity("version", vs)


def install_plugin(plugin_id: str, ctx=None):
    """
    Install a plugin

    Args:
        - plugin_id: UUID of plugin

    Returns:
        an error message object
    """
    return message.Message("works")


def uninstall_plugin(plugin_id: str, ctx=None):
    """
    Uninstall a plugin

    Args:
        - plugin_id: UUID of plugin

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
