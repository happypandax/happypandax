import os
import uuid
import sys
import traceback
import importlib
import inspect
import enum
import abc

from happypanda.common import exceptions, utils, constants, hlogger

log = hlogger.Logger(__name__)


def plugin_load(path, *args, **kwargs):
    """
    Attempts to load a plugin

    Params:
        - path -- path to plugin directory
        - *args -- additional arguments for plugin
        - **kwargs -- additional keyword arguments for plugin
    """
    args = ["test"]
    kwargs = {"1": 2}
    plugfile = None
    for f in os.scandir(path):
        if f.name.lower() == "hplugin.py":
            plugfile = f
            break
    if not plugfile:
        raise exceptions.CoreError(
            "Plugin loader",
            "No main entry file named 'HPlugin.py' found in '{}'".format(
                f.path))

    plug = os.path.splitext(plugfile.name)[0]
    sys.path.insert(0, os.path.realpath(path))
    try:
        _plugin_load(plug, path, *args, **kwargs)
    finally:
        sys.path.pop(0)


def _plugin_load(module_name_or_class, path, *args, **kwargs):
    """
    Imports plugin module and registers its main class

    Returns:
        PluginNode
    """
    plugclass = None
    if isinstance(module_name_or_class, str):
        mod = importlib.import_module(module_name_or_class)
        mod = importlib.reload(mod)
        plugmembers = inspect.getmembers(mod)
        for name, m_object in plugmembers:
            if name == "HPlugin":
                plugclass = m_object
                break
    elif inspect.isclass(module_name_or_class):
        plugclass = module_name_or_class
    if plugclass is None:
        raise exceptions.PluginError(
            "Plugin loader",
            "No main entry class named 'HPlugin' found in '{}'".format(path))
    log.i("Loading", plugclass.__name__)
    cls = HPluginMeta(
        plugclass.__name__,
        plugclass.__bases__,
        dict(
            plugclass.__dict__))
    return registered.register(cls, *args, **kwargs)


def plugin_loader(path, *args, **kwargs):
    """
    Scans provided paths for viable plugins and attempts to load them

    Params:
        - path -- path to directory of plugins
        - *args -- additional arguments for plugin
        - **kwargs -- additional keyword arguments for plugin

    """
    log.i('Loading plugins from path:', path)
    for pdir in os.scandir(path):
        plugin_load(pdir.path, *args, **kwargs)
    return registered.init_plugins()


def get_hook_return_type(return_list, return_type, assert_with=None):
    """
    A helper function to get the first returned type from plugins

    Returns:
        object or none
    """

    for x in return_list:
        if isinstance(x, return_type):
            if assert_with(x):
                return x

class HandlerValue:
    ""
    
    def __init__(self, name, handlers, *args, **kwargs):
        assert isinstance(handlers, (tuple, list))
        self.name = name
        self._handlers = handlers # (node, handler)
        self.args = args
        self.kwargs = kwargs
        self._failed = {} # { node : exception }

    def all(self):
        "Calls all handlers, returns tuple"
        failed = {}
        r = []
        for n, h in self._handlers:
            try:
                r.append(self._call_handler(n, h))
            except exceptions.PluginError as e:
                failed[n] = e
        self._failed.update(failed)

        # if all failed, raise error


        return tuple(r)

    def first(self):
        "Calls first handler, raises error if there is no handler"
        handler(*self.args, **self.kwargs)

    def first_or_none(self):
        "Calls first handler, return None if there is no handler"
        handler(*self.args, **self.kwargs)

    def last(self):
        "Calls last handler, raises error if there is no handler"
        handler(*self.args, **self.kwargs)

    def last_or_none(self):
        "Calls last handler, return None if there is no handler"
        handler(*self.args, **self.kwargs)

    def _raise_error(self):
        raise exceptions.PluginCommandError(self.name, "No handler is connected to this command")

    def _call_handler(self, node, handler):
        try:
            return handler(*self.args, **self.kwargs)
        except Exception as e:
            raise exceptions.PluginHandlerError(
                    n,"On command '{}' an exception was raised by plugin '{}:{}'\n\t{}".format(self.name, n.plugin.NAME, n.plugin.ID, e))



class PluginState(enum.Enum):
    Disabled = 0  # puporsely disabled
    Unloaded = 1  # unloaded because of dependencies, etc.
    Init = 2  # was just registered
    Enabled = 3  # plugin is loaded and in use
    Failed = 4 # failed because of error


class PluginNode:
    ""

    def __init__(self, plugin_class, *args, **kwargs):
        self.state = PluginState.Init
        self.plugin = plugin_class
        self.args = args
        self.kwargs = kwargs
        self.depends = {}  # {other_plugin_id : ( ver_start, vers_end )}
        self.commands = {}  # { command : handler }
        self.instanced = None
        self._list_depends()

    def _list_depends(self):
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
        return self.depends

    def _error_check(self, pluginid, plugin_class):
        ""
        if not hasattr(plugin_class, 'REQUIRE'):
            return None

        # invalid list
        if not isinstance(plugin_class.REQUIRE, (tuple, list)):
            e = exceptions.PluginAttributeError(
                plugin_class.NAME, "REQUIRE attribute must be a tuple/list")
            return False, e

        # empty list
        if not plugin_class.REQUIRE:
            return None

        # wrong list
        e = exceptions.PluginAttributeError(
            plugin_class.NAME,
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


class PluginManager:
    ""

    def __init__(self):
        self._nodes = {}
        self._started = False
        self._dirty = False
        self._commands = {} # { command : [ plugins ] }

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
            raise exceptions.PluginError(
                plugin.NAME, "Plugin ID already exists")
        node = PluginNode(plugin, *args, **kwargs)
        self._nodes[plugin.ID] = node
        return node

    def init_plugins(self):
        """
        Instantiate new plugins and (re)solve all dependencies

        Returns a dict with failed plugins: { plugin_id: exception }
        """

        failed = {}  # plugins with errors

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

            if node.state in (PluginState.Init, PluginState.Unloaded):
                self._init_plugin(plug_id)

        return failed

    def _solve(self, node, depends):
        ""
        for otherpluginid in depends:
            # check if required plugin is present
            if otherpluginid not in self._nodes:
                if self._nodes[otherpluginid].state == PluginState.Unloaded:
                    return exceptions.PluginError(
                        node.plugin.NAME, "A required plugin failed to load: {}".format(otherpluginid))
                elif self._nodes[otherpluginid].state == PluginState.Disabled:
                    return exceptions.PluginError(
                        node.plugin.NAME,
                        "A required plugin has been disabled: {}".format(otherpluginid))
                else:
                    return exceptions.PluginError(
                        node.plugin.NAME, "A required plugin is not present: {}".format(otherpluginid))

            vers = depends[otherpluginid]
            other_node = self._nodes[otherpluginid]
            # compare versions
            other_version = other_node.plugin.VERSION
            if not vers[0] <= other_version:
                return exceptions.PluginError(
                    node.plugin.NAME,
                    "A required plugin does not meet version requirement {} <= {}: {}".format(
                        vers[0],
                        other_version,
                        otherpluginid))
            if not vers[1] == (0, 0, 0) and not vers[1] > other_version:
                return exceptions.PluginError(
                    node.plugin.NAME,
                    "A required plugin does not meet version requirement {} > {}: {}".format(
                        vers[1],
                        other_version,
                        otherpluginid))
        return True

    def _init_plugin(self, pluginid):
        ""
        if pluginid in self._nodes:
            node = self._nodes[pluginid]
            try:
                self._ensure_valid_signature(node)
                node.instanced = node.plugin(*node.args, **node.kwargs)
            except Exception as e:
                self.disable_plugin(pluginid)
                if not isinstance(e, exceptions.PluginError):
                    raise exceptions.PluginError(node.plugin.NAME, "{}".format(e))
                raise
            node.state = PluginState.Enabled
        else:
            raise exceptions.CoreError(utils.this_function(), "Plugin node has not been registered with this manager")

    def _ensure_valid_signature(self, node):
        ""
        sig = inspect.signature(node.plugin.__init__)
        pars = list(sig.parameters)
        if not len(pars) == 3:
            raise exceptions.PluginSignatureError(node.plugin.NAME, "Unexpected __init__() signature")
        var_pos = False
        var_key = False
        for a in pars:
            if sig.parameters[a].kind == inspect.Parameter.VAR_POSITIONAL:
                var_pos = True
            elif sig.parameters[a].kind == inspect.Parameter.VAR_KEYWORD:
                var_key = True

        if not (var_pos and var_key):
            raise exceptions.PluginSignatureError(node.plugin.NAME, "A __init__ with the following signature must be defined: '__init__(self, *args, **kwargs)'")


    def disable_plugin(self, pluginid):
        "Remove plugin and its dependents"
        node = self._nodes[pluginid]
        node.state = PluginState.Disabled
        for cmd in node.commands:
            if cmd in self._commands:
                if node in self._commands[cmd]:
                    self._commands[cmd].remove(node)

    def on_command(self, command_name, *args, **kwargs):
        """
        Calls connected handlers returns HandlerValue
        """
        assert command_name in self._commands
        h = []
        for n in self._commands[command_name]:
            h.append((n, n.commands[command_name]))
        return HandlerValue(command_name, h, *args, **kwargs)


    def attach_to_command(self, node, command_name, handler):
        ""
        if not command_name in constants.available_commands:
            raise exceptions.PluginCommandError(node.plugin.NAME, "Command '{}' does not exist".format(command_name))
        if not callable(handler):
            raise exceptions.PluginCommandError(node.plugin.NAME, "Handler should be callable for command '{}'".format(command_name))

        # TODO: check signature

        node.commands[command_name] = handler
        if not command_name in self._commands:
            self._commands[command_name] = []
        self._commands[command_name].append(node)


    def attach_to_plugin_command(self, pluginid, node, command_name):
        ""
        raise NotImplementedError

    def _ensure_ready(self, node):
        ""
        assert isinstance(node, PluginNode)
        if not node.state == PluginState.Enabled:
            raise exceptions.PluginError(node.plugin.NAME, "This plugin is not ready")

    def _ensure_before_init(self, node):
        ""
        assert isinstance(node, PluginNode)
        if not node.state == PluginState.Init:
            raise exceptions.PluginError(node.plugin.NAME, "This method should be called in __init__")


constants.plugin_manager = registered = PluginManager()


class HPluginMeta(type):


    def __init__(cls, name, bases, dct):
        plugin_requires = ("ID", "NAME", "VERSION", "AUTHOR", "DESCRIPTION")

        for pr in plugin_requires:
            if not hasattr(cls, pr):
                raise exceptions.PluginAttributeError(
                    name, "{} attribute is missing".format(pr))

        try:
            uid = cls.ID.replace('-', '')
            val = uuid.UUID(uid, version=4)
            assert val.hex == uid
        except ValueError:
            raise exceptions.PluginIDError(
                name, "Invalid plugin id. UUID4 is required.")
        except AssertionError:
            raise exceptions.PluginIDError(
                name, "Invalid plugin id. A valid UUID4 is required.")

        if not isinstance(cls.NAME, str):
            raise exceptions.PluginAttributeError(
                name, "Plugin name should be a string")
        if not isinstance(cls.VERSION, tuple) or not len(cls.VERSION) == 3:
            raise exceptions.PluginAttributeError(
                name, "Plugin version should be a tuple with 3 integers")
        if not isinstance(cls.AUTHOR, str):
            raise exceptions.PluginAttributeError(
                name, "Plugin author should be a string")
        if not isinstance(cls.DESCRIPTION, str):
            raise exceptions.PluginAttributeError(
                name, "Plugin description should be a string")

        super().__init__(name, bases, dct)

        # set attributes
        attrs = inspect.getmembers(HPluginMeta)

        for n, a in attrs:
            if not n.startswith('_'):
                setattr(cls, n, a)

    def on_plugin_command(cls, pluginid, command_name, handler, **kwargs):
        """
        Attach handler to a command provided by a plugin

        Params:
            - pluginid -- PluginID of the plugin that has the command you want to attach to
            - command_name -- Name of the Class.command you want to connect to. Eg.: GalleryRename.rename
            - handler -- Your custom method that should be executed when command is invoked
        """
        raise NotImplementedError
        assert isinstance(command_name, str) and callable(handler) and isinstance(pluginid, str), ""
        node = registered._nodes.get(cls.ID)
        if not node:
            raise exceptions.PluginIDError(
                cls.NAME, "No plugin found with ID: {}".format(pluginid))
        registered._ensure_before_init(node)
        registered.attach_to_plugin_command(pluginid, node, command_name, handler)

    def on_command(cls, command_name, handler, **kwargs):
        """
        Attach handler to command

        Params:
            - command_name -- Name of the Class.command you want to connect to. Eg.: GalleryRename.rename
            - handler -- Your custom method that should be executed when command is invoked
        """

        assert isinstance(
            command_name, str) and callable(handler), ""
        node = registered._nodes.get(cls.ID)
        if not node:
            raise exceptions.PluginIDError(
                cls.NAME, "No plugin found with ID: {}".format(cls.ID))
        registered._ensure_before_init(node)
        registered.attach_to_command(node, command_name, handler)

    def create_command(cls, command_name, return_type):
        """
        Create a command that other plugins can attach to and extend
        After creation, the command can be used like a regular method: self.command_name(args, kwargs)

        Params:
            - command_name -- Name of the command you want to create.

        .. Note::
            The values returned by the handlers are returned in a tuple
        """
        raise NotImplementedError
