from happypanda.common import constants, message

def get_error(code, id, ctx=None):
    """
    Get error

    Params:
        - code -- error code, refer to ...
        - id -- 

    Returns:
        an error message object
    """
    return message.Message("works")

def install_plugin(plugin_id, ctx=None):
    """
    Install a plugin

    Params:
        - plugin_id -- UUID of plugin

    Returns:
        an error message object
    """
    return message.Message("works")

def uninstall_plugin(plugin_id, ctx=None):
    """
    Uninstall a plugin

    Params:
        - plugin_id -- UUID of plugin

    Returns:
        an error message object
    """
    return message.Message("works")

def list_plugins(ctx=None):
    """
    Get a list of available plugin information

    Returns:
        an error message object
    """
    return message.Message("works")
