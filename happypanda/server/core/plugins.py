import logging
import os
import uuid
import threading
import sys
import traceback
import importlib
from inspect import getmembers


from happypanda.common import exceptions

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical

def plugin_load(path, *args, **kwargs):
    """
    Attempts to load a plugin

    Params:
        - path -- path to plugin directory
        - *args -- additional arguments for plugin
        - **kwargs -- additional keyword arguments for plugin
    """
    plugfile = None
    for f in os.scandir(path):
        if f.name.lower() == "hplugin.py":
            plugfile = f
            break
    if not plugfile:
        raise exceptions.CoreError("Plugin loader", "No main entry file named 'HPlugin.py' found in '{}'".format(pdir.path))

    plug = os.path.splitext(plugfile.name)[0]
    sys.path.insert(0, os.path.realpath(path))
    try:
        mod = importlib.import_module(plug)
        mod = importlib.reload(mod)
        plugmembers = getmembers(mod)
        plugclass = None
        for name, m_object in plugmembers:
            if name == "HPlugin":
                plugclass = m_object
                break
        if not plugclass:
            raise exceptions.CoreError("Plugin loader", "No main entry class named 'HPlugin' found in '{}'".format(path))
        log_i("Loading {}".format(plugclass.__name__))
        cls = HPluginMeta(plugclass.__name__, plugclass.__bases__, dict(plugclass.__dict__))
        registered.register(cls, *args, **kwargs)
    finally:
        sys.path.pop(0)

def plugin_loader(path, *args, **kwargs):
    """
    Scans provided paths for viable plugins and attempts to load them

    Params:
        - path -- path to directory of plugins
        - *args -- additional arguments for plugin
        - **kwargs -- additional keyword arguments for plugin

    """
    log_i('Loading plugins from path: {}'.format(path))
    for pdir in os.scandir(path):
        plugin_load(pdir.path, *args, **kwargs)

class Plugins:
    ""
    _connections = set()
    _plugins = {}
    hooks = {}


    def register(self, plugin, *args, **kwargs):
        assert isinstance(plugin, HPluginMeta)
        self.hooks[plugin.ID] = {}
        self._plugins[plugin.ID] = plugin(*args, **kwargs)

    def _connectHooks(self):
        # TODO: make thread-safe with aqcuire & lock
        for pluginid, otherpluginid, hook_name, handler in self._connections:
            log_i("\t{}\n\tcreating connection to\n\t{}:{}".format(pluginid, hook_name, otherpluginid))
            self.hooks[otherpluginid][hook_name].addHandler(pluginid, handler)
        self._connections.clear()
        return True

    def __getattr__(self, key):
        try:
            return self._plugins[key]
        except KeyError:
            raise exceptions.PluginIDError("No plugin found with ID: {}".format(key))

registered = Plugins()

class HPluginMeta(type):

    def __init__(cls, name, bases, dct):
        if not name.endswith("HPlugin"):
            raise exceptions.PluginNameError(name, "Main plugin class should end with name HPlugin")

        if not hasattr(cls, "ID"):
            raise exceptions.PluginAttributeError(name, "ID attribute is missing")

        cls.ID = cls.ID.replace('-', '')
        if not hasattr(cls, "NAME"):
            raise exceptions.PluginAttributeError(name, "NAME attribute is missing")
        if not hasattr(cls, "VERSION"):
            raise exceptions.PluginAttributeError(name, "VERSION attribute is missing")
        if not hasattr(cls, "AUTHOR"):
            raise exceptions.PluginAttributeError(name, "AUTHOR attribute is missing")
        if not hasattr(cls, "DESCRIPTION"):
            raise exceptions.PluginAttributeError(name, "DESCRIPTION attribute is missing")

        try:
            val = uuid.UUID(cls.ID, version=4)
            assert val.hex == cls.ID
        except ValueError:
            raise exceptions.PluginIDError(name, "Invalid plugin id. UUID4 is required.")
        except AssertionError:
            raise exceptions.PluginIDError(name, "Invalid plugin id. A valid UUID4 is required.")

        if not isinstance(cls.NAME, str):
            raise exceptions.PluginAttributeError(name, "Plugin name should be a string")
        if not isinstance(cls.VERSION, tuple):
            raise exceptions.PluginAttributeError(name, "Plugin version should be a tuple with 3 integers")
        if not isinstance(cls.AUTHOR, str):
            raise exceptions.PluginAttributeError(name, "Plugin author should be a string")
        if not isinstance(cls.DESCRIPTION, str):
            raise exceptions.PluginAttributeError(name, "Plugin description should be a string")

        super().__init__(name, bases, dct)

        setattr(cls, "connectPlugin", cls.connectPlugin)
        setattr(cls, "newHook", cls.createHook)
        setattr(cls, "connectHook", cls.connectHook)
        #setattr(cls, "__getattr__", cls.__getattr__)

    def connectPlugin(cls, pluginid):
        """
        Connect to other plugins

        Params:
            - pluginid -- PluginID of the plugin you want to connect to

        Returns an object of the other plugin
        """
        name = cls.NAME

        class OtherHPlugin:

            def __init__(self, pluginid):
                self._id = pluginid.replace('-', '')
                if not registered._plugins.get(self._id):
                    raise exceptions.PluginIDError(name, "No plugin found with ID: " + self._id)
    
            def __getattr__(self, key):
                try:
                    plugin = registered._plugins[self._id]
                except KeyError:
                    raise exceptions.PluginIDError(name, "No plugin found with ID: " + self._id)
                    
                pluginmethod = registered.hooks[self.ID].get(key)
                if pluginmethod:
                    return pluginmethod 
                else:
                    raise exceptions.PluginMethodError(name, "Plugin {}:{} has no such method: {}".format(plugin.ID, plugin.NAME, key))

        return OtherHPlugin(pluginid)

    def connectHook(cls, pluginid, hook_name, handler):
        """
        Connect to other plugins' hooks

        Params:
            - pluginid -- PluginID of the plugin that has the hook you want to connect to
            - hook_name -- Exact name of the hook you want to connect to
            - handler -- Your custom method that should be executed when the other plugin uses its hook.
        """

        assert isinstance(pluginid, str) and isinstance(hook_name, str) and callable(handler), ""
        if not registered._plugins[pluginid]:
            raise exceptions.PluginIDError("No plugin found with ID: {}".format(pluginid))
        if not registered.hooks[pluginid][hook_name]:
            raise exceptions.PluginHookError("No hook with name '{}' found on plugin with ID: {}".format(hook_name, pluginid))
        registered._connections.append((cls.ID, pluginid.replace('-', ''), hook_name, handler))

    def createHook(cls, hook_name):
        """
        Create mountpoint that other plugins can hook to and extend

        Params:
            - hook_name -- Name of the hook you want to create.
        
        Hook should be invoked as such: self.hook_name(*args, **kwargs)
        Note: The values returned by the handlers are returned in a list
        """
        assert isinstance(hook_name, str), ""

        class Hook:
            owner = cls.ID
            _handlers = set()
            def addHandler(self, pluginid, handler):
                self._handlers.add((pluginid, handler))

            def __call__(self, *args, **kwargs):
                handler_returns = []
                for plugid, handler in self._handlers:
                    try:
                        handler_returns.append(handler(*args, **kwargs))
                    except Exception as e:
                        raise exceptions.PluginHandlerError(
                            "An exception occured in {}:{} by {}:{}\n\t{}".format(
                                hook_name, self.owner, registered._plugins[plugid].NAME, plugid, traceback.format_exc()))
                return handler_returns

        h = Hook()
        registered.hooks[cls.ID][hook_name] = h

#def startConnectionLoop():
#	def autoConnectHooks():
#		run = True
#		while run:
#			run = registered._connectHooks()
#	auto_t = threading.Thread(target=autoConnectHooks)
#	auto_t.start()