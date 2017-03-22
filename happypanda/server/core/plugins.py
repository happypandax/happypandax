import logging
import os
import uuid
import threading
import sys
import traceback
import importlib
import inspect


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
    args = ["test"]
    kwargs = {"1":2}
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
        _plugin_load(plug, path, *args, **kwargs)
    finally:
        sys.path.pop(0)

def _plugin_load(module_name, path, *args, **kwargs):
    "Imports plugin module and registers its main class"
    mod = importlib.import_module(module_name)
    mod = importlib.reload(mod)
    plugmembers = inspect.getmembers(mod)
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

    def __init__(self):
        self._started = False


    def register(self, plugin, *args, **kwargs):
        """
        Registers a plugin

        Params:
            - plugin -- main plugin class
            - *args -- additional arguments for plugin
            - **kwargs -- additional keyword arguments for plugin
        """
        assert isinstance(plugin, HPluginMeta)
        if plugin.ID in self._plugins:
            raise exceptions.PluginError(plugin.NAME, "Plugin ID already exists")
        self._plugins[plugin.ID] = (plugin, args, kwargs)

    def init_plugins(self):
        """
        Instantiate plugins and solve all dependencies

        Returns a dict with failed plugins: { plugin_id: exception }
        """

        failed = {} # plugins with errors
        all_plugins = {} # { plugin_id : {other_plugin_id : ( ver_start, vers_end )} }

        # list up all requirements
        for pluginid, args, kwargs in self._plugins:
            plugin_class = self._plugins[pluginid][0]
            if not hasattr(plugin_class, 'REQUIRE'):
                continue

            # invalid list
            if not isinstance(plugin_class.REQUIRE, (tuple, list)):
                failed[pluginid] = exceptions.PluginAttributeError(plugin_class.NAME,
                                                               "REQUIRE attribute must be a tuple/list")
                continue

            # empty list
            if not plugin_class.REQUIRE:
                continue

            # wrong list
            e = exceptions.PluginAttributeError(plugin_class.NAME,
                                                               "REQUIRE should look like this: [ ( ID, (0,0,0), (0,0,0) ) ]")
            if not all(isinstance(x, (tuple, list)) for x in plugin_class.REQUIRE):
                failed[pluginid] = e
                continue

            for x in plugin_class.REQUIRE:
                if not x:
                    failed[pluginid] = e
                    continue

                if len(x) < 2:
                    failed[pluginid] = e
                    continue

                if not isinstance(x[0], str):
                    failed[pluginid] = e
                    continue

                if not isinstance(x[1], tuple):
                    failed[pluginid] = e
                    continue

                version_end = (0, 0, 0)
                try:
                    if not isinstance(x[2], tuple):
                        failed[pluginid] = e
                        continue
                    version_end = x[2]
                except IndexError:
                    pass

                if not pluginid in all_plugins:
                    all_plugins[pluginid] = {}
                
                all_plugins[pluginid][x[0]] = (x[1], version_end)

        self._solve(failed, all_plugins)
        
        return failed

                


    def _solve(self, failed, all_plugins):
        ""
        s_plugins = []
        for pluginid in all_plugins:
            plugin_class = self._plugins[pluginid][0]
            fail = False

            for otherpluginid in all_plugins[pluginid]:
                # check if required plugin is present
                if not otherpluginid in self._plugins:
                    fail = True
                    failed[pluginid] = exceptions.PluginError(plugin_class.NAME, "A required plugin is not present: {}".format(otherpluginid))

                # check if required plugin failed to load
                if otherpluginid in failed:
                    fail = True
                    failed[pluginid] = exceptions.PluginError(plugin_class.NAME, "A required plugin failed to load: {}".format(otherpluginid))

                vers = all_plugins[pluginid][otherpluginid]
                otherplugin_class = self._plugins[otherpluginid][0]
                # compare versions
                other_version = otherplugin_class.VERSION
                if vers[0] <= other_version:
                    fail = True
                    failed[pluginid] = exceptions.PluginError(plugin_class.NAME,
                                                              "A required plugin does not meet version requirement {} <= {}: {}".format(vers[0], other_version, otherpluginid))
                
                if not vers[1] == (0, 0, 0) and vers[1] > other_version:
                    fail = True
                    failed[pluginid] = exceptions.PluginError(plugin_class.NAME,
                                                              "A required plugin does not meet version requirement {} > {}: {}".format(vers[1], other_version, otherpluginid))

            if fail:
                continue

            # all requirements fullfilled
            s_plugins.append(pluginid)

    def _init_plugin(self, pluginid):
        ""
        if pluginid in self._plugins:
            plugin, args, kwargs = self._plugins[pluginid]
            self.hooks = [pluginid]
            try:
                plug = plugin(*args, **kwargs)
            except TypeError:
                self.hooks.pop(plugin.ID)
                self._remove_plugin(pluginid)
                raise exceptions.PluginError(plugin.NAME, "A __init__ with the following signature must be defined: '__init__(*args, **kwargs)'")

    def _remove_plugin(self, pluginid):
        "Remove plugin and its dependents"
        pass

    def remove_plugin(self, plugin):
        ""
        pass

    def _connect_hooks(self):
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
            raise exceptions.PluginNameError(name, "Main plugin class should be named HPlugin")
        plugin_requires = ("ID", "NAME", "VERSION", "AUTHOR", "DESCRIPTION")

        for pr in plugin_requires:
            if not hasattr(cls, pr):
                raise exceptions.PluginAttributeError(name, "{} attribute is missing".format(pr))

        try:
            uid = cls.ID.replace('-', '')
            val = uuid.UUID(uid, version=4)
            assert val.hex == uid
        except ValueError:
            raise exceptions.PluginIDError(name, "Invalid plugin id. UUID4 is required.")
        except AssertionError:
            raise exceptions.PluginIDError(name, "Invalid plugin id. A valid UUID4 is required.")

        if not isinstance(cls.NAME, str):
            raise exceptions.PluginAttributeError(name, "Plugin name should be a string")
        if not isinstance(cls.VERSION, tuple) or not len(cls.VERSION) == 3:
            raise exceptions.PluginAttributeError(name, "Plugin version should be a tuple with 3 integers")
        if not isinstance(cls.AUTHOR, str):
            raise exceptions.PluginAttributeError(name, "Plugin author should be a string")
        if not isinstance(cls.DESCRIPTION, str):
            raise exceptions.PluginAttributeError(name, "Plugin description should be a string")

        super().__init__(name, bases, dct)

        # set attributes
        attrs = inspect.getmembers(HPluginMeta)

        setattr(cls, "__getattr__", cls.__getattr__)
        for n, a in attrs:
            if not n.startswith('_'):
                setattr(cls, n, a)

    #def require(cls, version_start, version_end=None, name='server'):
    #    """
    #    Add a core part as dependency, meaning if dependent core part is not available, this plugin will not load

    #    Params:
    #        - version_start -- A tuple of 3 ints. Require this core part is equal to or above this version.
    #        - version_end -- A tuple of 3 ints or None. Require this core part is below this version. 
    #        -- name -- which core part, available names are ['server', 'db']
    #    """
    #    pass

    #def require_plugin(cls, pluginid, version_start, version_end=None):
    #    """
    #    Add a plugin as dependency, meaning if dependent plugin is not available, this plugin will not load

    #    Params:
    #        - pluginid -- PluginID of the plugin you want to depend on
    #        - version_start -- A tuple of 3 ints. Require this plugin is equal to or above this version.
    #        - version_end -- A tuple of 3 ints or None. Require that plugin is below this version. 
    #    """
    #    pass
    #    # Note: load all pluginids and their versions first and then check for dependencies

    #def disable_plugin(cls, pluginid):
    #    """
    #    Shut's down and disallows a plugin from loading.

    #    Params:
    #        - pluginid -- PluginID of the plugin you want to disable
    #    """
    #    # Note: same as above, make a preliminary round for metadata ans such, add all disabled plugins
    #    #       in dict. Check if in disabled plugins before loading.

    def disable_hook(cls, pluginid, hook_name):
        """
        Disables a plugin's hook.

        Params:
            - pluginid -- PluginID of the plugin you want to disable a hook from
            - hook_name -- Exact name of the hook you want to disable
        """
        pass

    def connect_plugin(cls, pluginid):
        """
        Connect to other plugins

        Params:
            - pluginid -- PluginID of the plugin you want to connect to

        Returns:
            An object of the other plugin if it exists
        """
        name = cls.NAME

        class OtherHPlugin:

            def __init__(self, pluginid):
                self._id = pluginid
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

    def connect_hook(cls, pluginid, hook_name, handler):
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
        registered._connections.append((cls.ID, pluginid, hook_name, handler))

    def create_hook(cls, hook_name):
        """
        Create mountpoint that other plugins can hook to and extend
        After creation, the hook can be used like a regular method: self.hook_name(args, kwargs)

        Params:
            - hook_name -- Name of the hook you want to create.

        Returns:
            a callable hook object

        .. Note::
            The values returned by the handlers are returned in a list
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
        return

    def __getattr__(cls, key):
        try:
            h = registered.hooks[cls.ID].get(key)
            if not h:
                h = super().__getattr__(key)
            return h
        except AttributeError:
            raise exceptions.PluginMethodError(cls.NAME, "Plugin has no such attribute or hook '{}'".format(key))

#def startConnectionLoop():
#	def autoConnectHooks():
#		run = True
#		while run:
#			run = registered._connectHooks()
#	auto_t = threading.Thread(target=autoConnectHooks)
#	auto_t.start()