"""
The plugin interface module named ``__hpx__``.
Import it in your plugin to access the methods and classes defined by the module::
    
    import __hpx__ as hpx
    logger = hpx.get_logger(__name__)

In addition to what is defined here, :ref:`exceptions <Exceptions>` defined by HPX are also available at the module-level
and can be imported like so::

    import __hpx__ as hpx
    from __hpx__ import PluginError
    
    raise PluginError("", "")
    raise hpx.PluginError("", "")

"""
import typing
import functools

def get_logger(name: str):
    """
    Get the logger for this plugin

    Args:
        name: name of logger
    """
    return __manager__.get_plugin_logger(__plugin_id__, name)

def get_constant(name: str):
    """
    Get a value of a constant

    Args:
        name: name of constant
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
    Create a command entry that other plugins can attach to

    Args:
        f: command handler
        command: optional command name, if omitted, the name of the function will be used
    """
    if f is None or isinstance(f, str):
        command_name = f if isinstance(f, str) else command_name
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

def attach(f: typing.Callable=None, command: str=None):
    """
    Attach to a command entry

    Args:
        f: command handler
        command: a fully qualified command name, required
    """
    if f is None or isinstance(f, str):
        command = f if isinstance(f, str) else command
        def p_wrap(f):
            return attach(f, command)
        return p_wrap
    else:
        assert isinstance(command, str), "Command name must be the qualified name of a command"
        __manager__.attach_to_command(__plugin_id__, command, f)
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        return wrapper

def subscribe(f: typing.Callable=None, commandevent: str=None):
    """
    Subscribe to a command event

    Args:
        f: command event handler
        commandevent: a fully qualified command event name, required
    """
    if f is None or isinstance(f, str):
        commandevent = f if isinstance(f, str) else commandevent
        def p_wrap(f):
            return subscribe(f, commandevent)
        return p_wrap
    else:
        assert isinstance(commandevent, str), "Command event name must be the qualified name of a command event"
        __manager__.subscribe_to_event(__plugin_id__, commandevent, f)
        @functools.wraps(f)
        def wrapper(*args, **kwargs):
            return f(*args, **kwargs)
        return wrapper


__manager__ = None
__plugin_id__ = None
