import logging
import os
import uuid
import threading
import sys
import traceback
import importlib
import inspect
import enum


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
    """
    Imports plugin module and registers its main class
    
    Returns:
        PluginNode
    """
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
    return registered.register(cls, *args, **kwargs)

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
    return registered.init_plugins()

class PluginState(enum.Enum):
    Disabled = 0 # puporsely disabled
    Unloaded = 1 # unloaded because of dependencies, etc.
    Init = 2 # was just registered
    Enabled = 3 # plugin is loaded and in use

class PluginNode:
    ""
    def __init__(self, plugin_class, *args, **kwargs):
        self.state = PluginState.Init
        self.plugin = plugin_class
        self.args = args
        self.kwargs = kwargs
        self.depends = {} # {other_plugin_id : ( ver_start, vers_end )}
        self.hooks = {} # { hook_name : hook_method }
        self.instanced = None
        self.list_depends()

    def list_depends(self):
        ""
        pluginid = self.plugin.ID
        err = self._error_check(pluginid, self.plugin)
        if err is None:
            return
        if isinstance(err, tuple):
                raise err[1]

        for x in self.plugin.REQUIRE:
            version_end = (0, 0, 0)
            try:
                version_end = x[2]
            except IndexError:
                pass

            self.depends[x[0]] = (x[1], version_end)

    def _error_check(self, pluginid, plugin_class):
        ""
        if not hasattr(plugin_class, 'REQUIRE'):
            return None

        # invalid list
        if not isinstance(plugin_class.REQUIRE, (tuple, list)):
            e = exceptions.PluginAttributeError(plugin_class.NAME,
                                                            "REQUIRE attribute must be a tuple/list")
            return False, e

        # empty list
        if not plugin_class.REQUIRE:
            return None

        # wrong list
        e = exceptions.PluginAttributeError(plugin_class.NAME,
                                                            "REQUIRE should look like this: [ ( ID, (0,0,0), (0,0,0) ) ]")
        if not all(isinstance(x, (tuple, list)) for x in plugin_class.REQUIRE):
            return False, e

        for x in plugin_class.REQUIRE:
            if not x:
                return False, e

            if len(x) < 2:
                return False, e

            if not isinstance(x[0], str):
                return False, e

            if not isinstance(x[1], tuple):
                return False, e

            try:
                if not isinstance(x[2], tuple):
                    return False, e
            except IndexError:
                pass

        return True

    def __eq__(self, other):
        return other == self.plugin.ID

    def __hash__(self):
        return hash(self.plugin.ID)

class Plugins:
    ""
    _connections = set()
    _nodes = {}

    def __init__(self):
        self._started = False
        self._dirty = False


    def register(self, plugin, *args, **kwargs):
        """
        Registers a plugin

        Params:
            - plugin -- main plugin class
            - *args -- additional arguments for plugin
            - **kwargs -- additional keyword arguments for plugin

        Returns:
            PluginNode
        """
        assert isinstance(plugin, HPluginMeta)
        if plugin.ID in self._nodes:
            raise exceptions.PluginError(plugin.NAME, "Plugin ID already exists")
        node = PluginNode(plugin, *args, **kwargs)
        self._nodes[plugin.ID] = node
        return node

    def init_plugins(self):
        """
        Instantiate new plugins and (re)solve all dependencies

        Returns a dict with failed plugins: { plugin_id: exception }
        """

        failed = {} # plugins with errors

        # list up all requirements
        for plug_id in self._nodes:
            node = self._nodes[plug_id]
            if node.state == PluginState.Disabled:
                continue

            result = self._solve(node, node.depends)
            if isinstance(result, Exception):
                failed[node.plugin.ID] = result
                node.state = PluginState.Unloaded
                continue

            if node.state == PluginState.Init:
                self._init_plugin(node)

        self._connect_hooks()
                
        return failed
                
    def _solve(self, node, depends):
        ""
        for otherpluginid in depends:
            # check if required plugin is present
            if not otherpluginid in self._nodes:
                if self._nodes[otherpluginid].state == PluginState.Unloaded:
                    return exceptions.PluginError(node.plugin.NAME, "A required plugin failed to load: {}".format(otherpluginid))
                elif self._nodes[otherpluginid].state == PluginState.Disabled:
                    return exceptions.PluginError(node.plugin.NAME, "A required plugin has been disabled: {}".format(otherpluginid))
                else:
                    return exceptions.PluginError(node.plugin.NAME, "A required plugin is not present: {}".format(otherpluginid))

            vers = depends[otherpluginid]
            other_node = self._nodes[otherpluginid]
            # compare versions
            other_version = other_node.plugin.VERSION
            if not vers[0] <= other_version:
                return exceptions.PluginError(node.plugin.NAME,
                                                            "A required plugin does not meet version requirement {} <= {}: {}".format(vers[0], other_version, otherpluginid))
            if not vers[1] == (0, 0, 0) and not vers[1] > other_version:
                return exceptions.PluginError(node.plugin.NAME,
                                                            "A required plugin does not meet version requirement {} > {}: {}".format(vers[1], other_version, otherpluginid))
        return True

    def _init_plugin(self, pluginid):
        ""
        if pluginid in self._nodes:
            node = self._nodes[pluginid]
            try:
                node.instanced = node.plugin(*node.args, **node.kwargs)
            except TypeError: # TODO: revise.. inspect method signature?
                self.disable_plugin(pluginid)
                raise exceptions.PluginError(node.plugin.NAME, "A __init__ with the following signature must be defined: '__init__(self, *args, **kwargs)'")
            except Exception as e:
                raise exceptions.PluginError(node.plugin.NAME, "{}".format(e))
            node.state = PluginState.Enabled

    def disable_plugin(self, pluginid):
        "Remove plugin and its dependents"
        node = self._nodes[pluginid]
        node.state = PluginState.Disabled

    def add_connection(self, pluginid, otherpluginid, hook_name, handler):
        ""
        self._connections.add((pluginid, otherpluginid, hook_name, handler))
        self._dirty = True

    def _call_handler(self, handler, *args, **kwargs):
        ""
        if self._dirty:
            self._connect_hooks()
        return handler(*args, **kwargs)

    def _connect_hooks(self):
        s = self._connections.copy()
        while len(s):
            pluginid, otherpluginid, hook_name, handler = s.pop()
            log_i("\t{}\n\tcreating connection to\n\t{}:{}".format(pluginid, hook_name, otherpluginid))
            node = self._nodes[otherpluginid]
            if not node.hooks.get(hook_name):
                raise exceptions.PluginHookError("Plugin Connections", "No hook with name '{}' found on plugin with ID: {} requested by {}".format(hook_name, otherpluginid, pluginid)) # TODO: use names
            node.hooks[hook_name].addHandler(pluginid, handler)
        self._connections.difference_update(s)

    def __getattr__(self, key):
        try:
            return self._nodes[key]
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

    #def disable_plugin(cls, pluginid):
    #    """
    #    Shut's down and disallows a plugin from loading.

    #    Params:
    #        - pluginid -- PluginID of the plugin you want to disable
    #    """

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
                self.ID = pluginid
                if not registered._nodes.get(self.ID):
                    raise exceptions.PluginIDError(name, "No plugin found with ID: " + self.ID)
    
            def __getattr__(self, key):
                try:
                    node = registered._nodes[self.ID]
                except KeyError:
                    raise exceptions.PluginIDError(name, "No plugin found with ID: " + self.ID)
                
                pluginmethod = node.hooks.get(key)
                if not pluginmethod:
                    raise exceptions.PluginMethodError(name, "Plugin {}:{} has no such method: {}".format(node.plugin.NAME, node.plugin.ID, key))
                return pluginmethod

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
        node = registered._nodes.get(pluginid)
        if not node:
            raise exceptions.PluginIDError(cls.NAME, "No plugin found with ID: {}".format(pluginid))
        registered.add_connection(cls.ID, pluginid, hook_name, handler)

    def create_hook(cls, hook_name):
        """
        Create mountpoint that other plugins can hook to and extend
        After creation, the hook can be used like a regular method: self.hook_name(args, kwargs)

        Params:
            - hook_name -- Name of the hook you want to create.

        .. Note::
            The values returned by the handlers are returned in a tuple
        """
        assert isinstance(hook_name, str), ""

        class Hook:
            owner = cls.ID
            _handlers = {}
            def addHandler(self, pluginid, handler):
                assert isinstance(pluginid, str) and callable(handler)
                if not pluginid in self._handlers:
                    self._handlers[pluginid] = set()
                self._handlers[pluginid].add(handler)

            def __call__(self, *args, **kwargs):
                handler_returns = []
                for plugid in self._handlers:
                    for handler in self._handlers[plugid]:
                        try:
                            handler_returns.append(registered._call_handler(handler, *args, **kwargs))
                        except Exception as e:
                            raise exceptions.PluginHandlerError(
                                "An exception occured in {}:{} by {}:{}\n\t{}".format(
                                    hook_name, self.owner, registered._nodes[plugid].NAME, plugid, traceback.format_exc()))
                return tuple(handler_returns)

        h = Hook()
        registered._nodes[cls.ID].hooks[hook_name] = h

    def __getattr__(cls, key):
        try:
            node = registered._nodes.get(cls.ID)
            if node:
                h = node.hooks.get(key)
                if h:
                    return h

            return super().__getattr__(key)
        except AttributeError:
            raise exceptions.PluginMethodError(cls.NAME, "Plugin has no such attribute or hook '{}'".format(key))

#def startConnectionLoop():
#	def autoConnectHooks():
#		run = True
#		while run:
#			run = registered._connectHooks()
#	auto_t = threading.Thread(target=autoConnectHooks)
#	auto_t.start()