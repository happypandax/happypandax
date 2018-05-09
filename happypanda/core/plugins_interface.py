"""
Hello world
"""
import functools
import typing

def get_logger(name: str):
    """
    Get the logger for this plugin

    Args:
        name: name of logger
    """
    return __manager__.get_plugin_logger(__plugin_id__, name)

def get_exception(name: str):
    """
    Get an exception object defined by HPX

    Args:
        name: name of exception
    """
    pass

def get_config():
    """
    Get a dict-like object with configuration specific to this plugin

    Returns:
        dict-like object
    """
    pass

def get_setting(name: str):
    """
    Get a dict-like object with configuration specific to this plugin
    """

def save_config(obj: dict):
    """
    Save configuration specific to this plugin

    Args:
        obj: dict-like object
    """
    pass

def command(f: typing.Callable=None, command_name: str=None):
    """
    Create a command entry that other plugins can subscribe to

    Args:
        f: command handler
        command: optional command name, if omitted, the name of the function will be used
    """
    if f is None:
        def p_wrap(f):
            return command(f, command_name)
        return p_wrap
    else:
        assert isinstance(command_name, str), "Command name must be of type str"
        raise NotImplementedError
        # TODO: create plugin command
        #__manager__.subscribe_to_command(plugin_id, command, f)
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            pass
            # TODO: call command through pm
            #__manager__.call_command(plugin_id, command, f)
            
            # return HandlerValue?
        return wrapper

def subscribe(f: typing.Callable=None, command: str=None):
    """
    Subscribe to a command

    Args:
        f: command handler
        command: a fully qualified command name, required
    """
    if f is None:
        def p_wrap(f):
            return subscribe(f, command)
        return p_wrap
    else:
        assert isinstance(command, str), "Command must be the qualified name of a command"
        __manager__.subscribe_to_command(__plugin_id__, command, f)
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        return wrapper

__manager__ = None
__plugin_id__ = None
__globals__ = None