"""
Interface
----------------------------------------

The plugin interface module is named ``__hpx__``.
Import it in your plugin to access the methods and classes defined by the module::

    import __hpx__ as hpx
    logger = hpx.get_logger(__name__)

In addition to what is defined here, :ref:`exceptions <Exceptions>` and :ref:`enums <Enums>` defined by HPX are also available at the module-level
and can be imported like so::

    import __hpx__ as hpx
    from __hpx__ import PluginError, PluginState
    print(PluginState) # -> <enum 'PluginState'>
    print(hpx.ImageSize) # -> <enum 'ImageSize'>
    raise PluginError("", "")
    raise hpx.PluginError("", "")

**command**

The object ``command`` is available on the module-level and provides access to the various different commands defined by HPX::

    from __hpx__ import command
    command.CheckUpdate()


See :ref:`Commands` for all the various commands available information.

-----------------------------------------------------------------------

**constants**

The object ``constants`` is available on the module-level and provides various useful constant values.::

    from __hpx__ import constants
    print(constants.version) # -> (0, 0, 0)

.. exec::

    from happypanda.core.plugins import PluginConstants

    print(PluginConstants.__doc__)

    p = PluginConstants()
    for x in sorted(p.__dict__):
        y = p.__dict__[x]
        print("    **{}** : *{}* = {}".format(x, type(y).__name__, y))

-----------------------------------------------------------------------

"""

import typing
import functools

database = None
command = None
constants = None


class _NO_DEFAULT:
    pass


def get_logger(name: str=None):
    """
    Get the :class:`logging.Logger` object for this plugin

    Args:
        name: name of logger
    """
    return __manager__.get_plugin_logger(__plugin_id__, name)


def get_config():
    """
    Get a dict-like object with configuration specific to this plugin

    Returns:
        dict-like object
    """
    return __manager__.get_plugin_config(__plugin_id__)


def get_setting(namespace: str, key: str, default=_NO_DEFAULT):
    """
    Get the value of any setting in the configuration. See :ref:`Settings`.

    Args:
        namespace: setting namespace
        key: setting key
        default: default value if no key was found

    Returns:
        value of setting or default value if default was set, else raise a KeyError
    """
    try:
        return __manager__.get_setting(__plugin_id__, namespace, key)
    except KeyError:
        if default is _NO_DEFAULT:
            raise
        return default


def save_config(obj: dict):
    """
    Save configuration specific to this plugin

    The configuration will appear in the ``plugin.<plugin namespace>`` namespace.
    ``<plugin namespace>`` is equal to ``<plugin shortname>.<2nd item in plugin id>.
    For example: ``myplugin.eca3`` where ``eca3`` is from ``xxxxxxx-eca3-xxxx-xxxx-xxxxxxxxxxxx``

    Args:
        obj: dict-like object

    Returns:
        bool on if config was saved
    """
    assert isinstance(obj, dict)
    return __manager__.save_plugin_config(__plugin_id__, obj)


# def create_command(f: typing.Callable=None, command_name: str=None):
#    """
#    Create a command entry that other plugins can attach a handler to

#    Args:
#        f: command handler
#        command: optional command name, if omitted, the name of the function will be used
#    """
#    if f is None or isinstance(f, str):
#        command_name = f if isinstance(f, str) else command_name

#        def p_wrap(f):
#            return command(f, command_name)
#        return p_wrap
#    else:
#        assert isinstance(command_name, str), "Command name must be of type str"
#        raise NotImplementedError
#        # TODO: create plugin command
#        #__manager__.subscribe_to_command(plugin_id, command, f)

#        @functools.wraps(f)
#        def wrapper(*args, **kwargs):
#            pass
#            # TODO: call command through pm
#            #__manager__.call_command(plugin_id, command, f)

#            # return HandlerValue?
#        return wrapper


def attach(f: typing.Callable=None, command: str=None):
    """
    Attach a handler to a command entry

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
    Subscribe a handler to a command event

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
