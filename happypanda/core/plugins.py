import os
import uuid
import sys
import importlib
import inspect
import enum
import logging
import gevent
import json
import glob
import copy
import logging

from packaging.requirements import Requirement, InvalidRequirement
from packaging.specifiers import Specifier, InvalidSpecifier
from packaging import markers
from packaging.version import Version, InvalidVersion
from gevent.event import Event
from collections import OrderedDict
from logging.handlers import RotatingFileHandler
from contextlib import contextmanager

from happypanda.interface.enums import PluginState
from happypanda.common import exceptions, utils, constants, hlogger, config
from happypanda.core import plugins_interface, async_utils

log = hlogger.Logger(constants.log_ns_plugin + __name__)

# add hpx marker
markers.VARIABLE |= markers.L("hpx")
markers.VARIABLE |= markers.L("happypandax")
markers.ALIASES['hpx'] = "happypandax"

@contextmanager
def log_plugin_error(logger, exception=True):
    assert isinstance(logger, logging.Logger) or logger is None
    try:
        yield
    except exceptions.PluginError as e:
        if logger:
            h = logger.exception if exception else logger.error
            h("{}: {}".format(e.__class__.__name__, e.msg))
        else:
            log.w("PluginError: {} -- {}".format(e.where, e.msg))


def format_plugin(node):
    ""
    assert isinstance(node, (PluginNode, str))

    txt = ""

    if isinstance(node, str):
        txt = node
    else:
        txt = "{}:{}".format(node.info.shortname, node.info.id)

    return txt

plugin_logs = {}

class PluginFilter:
    """
    Reduces error and critical levels to warning
    """

    def filter(self, record):
        if not __file__ == record.pathname:
            log_name = constants.log_ns_plugin + 'context.' + record.name[len(constants.log_ns_plugincontext):]
            levels = {logging.ERROR:logging.WARNING,
                      logging.CRITICAL:logging.WARNING}
            r = copy.copy(record)
            r.levelno = levels.get(r.levelno, r.levelno)
            r.levelname = logging.getLevelName(r.levelno)
            r.name = log_name
            plugin_logs.setdefault(log_name, hlogger.Logger(log_name)).handle(r)
        return True

def get_plugin_logger(name, *handler, propogate=False):
    assert name and isinstance(name, str)
    l = logging.getLogger(constants.log_ns_plugincontext+name)
    l.addFilter
    l.propagate = propogate
    if not l.hasHandlers():
        for h in handler:
            l.addHandler(h)
    return l

def create_plugin_logger(plugin_dir):
    "Create a logger for plugin"
    log_handlers = []
    formatter = logging.Formatter(constants.log_plugin_format, constants.log_datefmt)
    plugin_dir = os.path.join(plugin_dir, "logs")
    os.makedirs(plugin_dir, exist_ok=True)
    log_path = os.path.join(plugin_dir, "plugin.log")
    try:
        with open(log_path, 'x') as f:  # noqa: F841
            pass
    except FileExistsError:
        pass
    normal_handler = RotatingFileHandler(
        log_path,
        maxBytes=constants.log_size,
        encoding='utf-8',
        backupCount=1)
    normal_handler.setLevel(logging.INFO)
    normal_handler.setFormatter(formatter)
    normal_handler.addFilter(PluginFilter())
    log_handlers.append(normal_handler)

    if config.debug.value:
        log_debug_path = os.path.join(plugin_dir, "plugin_debug.log")
        try:
            with open(log_debug_path, 'x') as f:  # noqa: F841
                pass
        except FileExistsError:
            pass
        debug_handler = logging.FileHandler(log_debug_path, 'w', 'utf-8')
        debug_handler.setLevel(logging.DEBUG)
        debug_handler.setFormatter(formatter)
        log_handlers.append(debug_handler)


    return log_handlers


def plugin_load(plugin_manager, path):
    """
    Attempts to load a plugin

    Params:
        - path -- path to plugin directory
    """
    pname = os.path.split(path)[1]
    log_handlers = create_plugin_logger(path)
    plug_log = get_plugin_logger('loading.'+pname, *log_handlers)
    plug_log.debug("Attempting to load plugin at: {}".format(path))
    with log_plugin_error(plug_log, False):
        manifest = None
        for f in os.scandir(path):
            if f.name.lower() == "hplugin.json":
                manifest = f.path
                break
        if not manifest:
            raise exceptions.PluginLoadError(
                pname,
                "No manifest file named 'HPlugin.json' found in plugin directory '{}'".format(path))
        return _plugin_load(plugin_manager, manifest, path, plug_log)


def _plugin_load(plugin_manager, manifest, path, logger=None):
    """
    Imports plugin module and registers its main class

    Returns:
        manifest dict
    """
    assert isinstance(manifest, str)
    pname = os.path.split(path)[1]
    with log_plugin_error(logger, False):
        with open(manifest, 'r', encoding='utf-8') as f:
            err = None
            try:
                manifest = json.load(f)
            except json.JSONDecodeError as e:
                err = exceptions.PluginLoadError(
                    pname,
                    "Failed to decode manifest file: {}".format(e.args[0]))
            if err: raise err
        pentry = manifest.get("entry")
        if pentry:
            if not os.path.exists(os.path.join(path, pentry)):
                raise exceptions.PluginLoadError(pname, "Plugin entry '{}' does not exist".format(pentry))
        ptest = manifest.get("test")
        if ptest:
            if not os.path.exists(os.path.join(path, ptest)):
                raise exceptions.PluginLoadError(pname, "Plugin test entry '{}' does not exist".format(ptest))
        manifestobj = PluginManifest(manifest, path)
        return plugin_manager.register(manifestobj)


def plugin_loader(plugin_manager, path):
    """
    Scans provided paths for viable plugins and attempts to load them

    Params:
        - path -- path to directory of plugins

    """
    assert isinstance(plugin_manager, PluginManager)
    log.i('Loading plugins from path:', path)
    plugindirs = list(os.scandir(path))
    log.i("Loading", len(plugindirs), "plugins", stdout=True)
    for pdir in plugindirs:
        gevent.spawn(plugin_load, plugin_manager, pdir.path).join()
    plugin_manager.wake_up()

class PluginManifest(OrderedDict):

    def __init__(self, manifest, path=""):
        assert isinstance(manifest, dict)
        manifest['path'] = path
        name = "Plugin loader"
        plugin_requires = ("id", "entry", "name", "shortname", "version", "author", "description")

        for pr in plugin_requires:
            if manifest.get(pr) is None:
                raise exceptions.PluginAttributeError(
                    name, "{} attribute is missing or null".format(pr))

        for pr in plugin_requires:
            if not manifest.get(pr):
                raise exceptions.PluginAttributeError(
                    name, "{} attribute cannot be empty".format(pr))

        try:
            uid = manifest.get("id").replace('-', '')
            val = uuid.UUID(uid, version=4)
            assert val.hex == uid
        except (ValueError, AssertionError):
            raise exceptions.PluginAttributeError(
                name, "Invalid plugin id. A valid UUID4 is required.")

        if not isinstance(manifest.get('name'), str):
            raise exceptions.PluginAttributeError(
                name, "Plugin name should be a string")
        if not isinstance(manifest.get('entry'), str):
            raise exceptions.PluginAttributeError(
                name, "Plugin entry should be a filename")
        if not isinstance(manifest.get('shortname'), str):
            raise exceptions.PluginAttributeError(
                name, "Plugin shortname should be a string")
        if len(manifest.get('shortname')) > constants.plugin_shortname_length:
            raise exceptions.PluginAttributeError(
                name, "Plugin shortname cannot exceed {} characters".format(constants.plugin_shortname_length))
        manifest['shortname'] = manifest['shortname'].strip()
        if ' ' in manifest.get('shortname'):
            raise exceptions.PluginAttributeError(
                name, "Plugin shortname must not contain any whitespace")
        if not manifest.get('shortname').islower():
            raise exceptions.PluginAttributeError(
                name, "Plugin shortname should be all lowercase")
        if not isinstance(manifest.get('version'), str):
            raise exceptions.PluginAttributeError(
                name, "Plugin version should be a string")
        try:
            manifest['version'] = Version(manifest['version'])
        except InvalidVersion:
            raise exceptions.PluginAttributeError(
                name, "Plugin version should conform to PEP 440")
        if not isinstance(manifest.get('author'), str):
            raise exceptions.PluginAttributeError(
                name, "Plugin author should be a string")
        if not isinstance(manifest.get('description'), str):
            raise exceptions.PluginAttributeError(
                name, "Plugin description should be a string")

        if manifest.get('website'):
            if not isinstance(manifest.get('website'), str):
                raise exceptions.PluginAttributeError(
                    name, "Plugin website should be a string")

        if manifest.get('test'):
            if not isinstance(manifest.get('test'), str):
                raise exceptions.PluginAttributeError(
                    name, "Plugin test entry should be a filename")

        if manifest.get('require'):
            if not isinstance(manifest.get('require'), list):
                raise exceptions.PluginAttributeError(
                    name, "Plugin require should be a list of strings")
            require = manifest['require'][:]
            manifest['require'] = []
            for x in require:
                err = None

                if not isinstance(x, str):
                    raise exceptions.PluginAttributeError(
                        name, "Plugin require should be a list of strings")
                try:
                    r = Requirement(x)
                except InvalidRequirement as e:
                    err = exceptions.PluginAttributeError(
                        name, "{} on '{}'".format(e.args[0], x))

                if err: raise err
                
                if r.name in markers.VARIABLE:
                    try:
                        if r.marker:
                            raise exceptions.PluginAttributeError(
                                name, "Requirement '{}' cannot contain a marker".format(x))
                        try:
                            s = Specifier(str(r.specifier))
                            m = "{}{}'{}'".format(r.name, s.operator, s.version)
                            r.marker = markers.Marker(m)
                        except InvalidSpecifier:
                            r.marker = markers.Marker(x)

                    except (markers.InvalidMarker, InvalidSpecifier) as e:
                        err = exceptions.PluginAttributeError(
                            name, "Invalid requirement '{}': {}".format(x, e.args[0]))

                if err: raise err

                manifest['require'].append(r)

        super().__init__(manifest)

    def __getattr__(self, key):
        if key in self:
            return self[key]
        raise AttributeError("AttributeError: no attribute named '{}'".format(key))


class HandlerValue:
    ""

    def __init__(self, name, handlers, *args, **kwargs):
        assert isinstance(handlers, (tuple, list))
        self.name = name
        self._handlers = handlers  # [ (node, handler) ]
        self.args = args
        self.kwargs = kwargs
        self.failed = {}  # { node : exception }

        self.default_capture_handlers = {}  # { token : handler }
        self._capture_handlers = {}  # { token : (node, handler) }
        self.capture = False
        self.capture_token = '*'

        self.expected_type = None
        self.default_handler = None

        for n, h in self._handlers:
            self._add_capture_handler(h, n)

    def default(self):
        "Calls the default handler"
        if not self.default_handler:
            raise self._raise_default_error()

        return self.default_handler(*self.args, **self.kwargs)

    def default_capture(self, token):
        "Calls the default capture handler"
        raise NotImplementedError

    def all(self, default=False):
        "Calls all handlers, returns tuple"
        if self.capture:
            r = self._call_capture(None, False, default)
            if r is None:
                return tuple()
            return r
        else:
            r = []
            for n, h in self._handlers:
                x = self._call_handler(n, h)
                if x is not None:
                    r.append(x)

            if (not r and self.default_handler) or (
                    default and self.default_handler):
                r.append(self.default_handler(*self.args, **self.kwargs))

            return tuple(r)

    def get_handlers(self):
        return tuple(x[1] for x in self._handlers)

    def get_node(self, idx):
        return self._handlers[idx][0]

    def first(self):
        "Calls first handler, raises error if there is no handler"
        return self._call_node_idx(0, True)

    def first_or_none(self):
        "Calls first handler, return None if there is no handler"
        return self._call_node_idx(0, False)

    def last(self):
        "Calls last handler, raises error if there is no handler"
        return self._call_node_idx(-1, True)

    def last_or_none(self):
        "Calls last handler, return None if there is no handler"
        return self._call_node_idx(-1, False)

    def _add_capture_handler(self, handler, node=None):
        assert callable(handler)
        assert node is None or isinstance(PluginNode)

        capture_dict = self._capture_handlers
        if not node:
            capture_dict = self.default_capture_handlers

        sig = inspect.signature(handler)

        if 'capture' in sig.parameters:
            cap = sig.parameters['capture'].default

            if not cap == inspect._empty:

                if not isinstance(cap, (list, tuple)):
                    cap = (cap,)

                for c in cap:
                    if c not in capture_dict:
                        capture_dict[c] = []

                    if node:
                        capture_dict[c].append((node, handler))
                    else:
                        capture_dict[c].append(handler)

    def _raise_error(self):
        raise exceptions.CoreError(
            self.name,
            "No handler is connected to this command: {} (capture token: {})".format(self.name, self.capture_token))

    def _raise_default_error(self):
        raise exceptions.CoreError(
            self.name,
            "No default handler is connected to this command: {} (capture token: {})".format(self.name, self.capture_token))

    def _call_capture(self, idx, error, default):
        if not self._capture_handlers and not self.default_capture_handlers:
            if error:
                self._raise_error()
            return None

        token_exists = self.capture_token in self._capture_handlers
        token_exists_d = self.capture_token in self.default_capture_handlers

        if not token_exists and not token_exists_d:
            if error:
                self._raise_error()
            return None

        token_handler = None
        token_handler_d = None

        if token_exists:
            token_handler = self._capture_handlers[self.capture_token]

        if token_exists_d:
            token_handler_d = self.default_capture_handlers[self.capture_token]

        if not token_handler and not token_handler_d:
            if error:
                self._raise_error()
            return None

        r = []

        if token_handler:
            if idx is not None:
                return self._call_handler(*token_handler[idx])
            else:
                tuple(r.append(self._call_handler(*y)) for y in token_handler)

        if token_handler_d:
            if idx is not None:
                return token_handler_d[0](*self.args, **self.kwargs)
            else:
                if default or not token_handler:
                    tuple(r.append(y(*self.args, **self.kwargs))
                          for y in token_handler_d)

        return tuple(x for x in r if x is not None)

    def _call_node_idx(self, idx, error=False):
        if self.capture:
            return self._call_capture(idx, error, False)
        else:
            if not self._handlers:
                if self.default_handler:
                    return self.default_handler(*self.args, **self.kwargs)
                if error:
                    self._raise_error()
                return None
            return self._call_handler(*self._handlers[idx])

    def _call_handler(self, node, handler):
        with log_plugin_error(node.logger, False):
            err = None
            try:
                r = node.call_handler(handler, self.args, self.kwargs)

                if self.expected_type is not None:
                    if not isinstance(r, self.expected_type):
                        raise exceptions.PluginHandlerError(
                            node,
                            "On command '{}' expected type '{}', but got '{}' by plugin handler '{}'".format(
                                self.name, str(type(self.expected_type)), str(type(r)), node.format()))

            except Exception as e:
                self.failed[node] = e
                if isinstance(e, exceptions.PluginError):
                    raise
                else:
                    node.logger.exception("An unhandled exception was raised by plugin handler on command '{}'".format(self.name))


class PluginNode:
    ""

    def __init__(self, manager, manifest):
        self.state = PluginState.Registered
        self.manager = manager
        self.info = manifest
        self.commands = {}  # { command : handler }
        self._modules = []
        self._isolate = None
        self.dependencies = set()
        self.dependents = set()
        self._evaluation = None
        self.status = ""
        self.logger = get_plugin_logger(self.info.shortname, *create_plugin_logger(self.info.path))


    def init(self):
        log.i("Initiating plugin -", self.format())
        self.logger.info("Initiating plugin")
        self._isolate = PluginIsolate(self)
        err = None
        entry_file = os.path.join(self.info.path, self.info.entry)
        with open(entry_file) as f:
            try:
                with self._isolate as i:
                    exec(f.read(), i.plugin_globals)
            except Exception as e:
                err = e
                self.logger.exception("An unhandled exception was raised during plugin initialization")
        return False if err else True

    def add_handler(self, command, handler):
        self.logger.debug(log.d("Adding command handler to", command, "-", self.format()))
        self.commands[command] = handler

    def call_handler(self, handler, args, kwargs):
        log.d("Calling command handler '{}' -".format(handler.__name__), self.format())
        self.logger.info("Calling command handler '{}'".format(handler.__name__))
        with self._isolate:
            return handler(*args, *kwargs)

    def unload(self, reason=""):
        if self.state == PluginState.Unloaded:
            return
        log.d("Unloading plugin -", self.format())
        self.logger.info("Unloading plugin")
        self.status = reason
        self.manager.disable_plugin(self)
        self.state = PluginState.Unloaded
        for n in self.dependents:
            n.unload("Plugin '{}' was unloaded".format(self.info.shortname))

    def evaluate(self):
        "Evaluate markers, returns false if plugin was unloaded"
        if self._evaluation is not None:
            return self._evaluation
        unloaded = False
        for r in self.info.require.copy():
            fail = False
            try:
                if r.marker:
                    fail = not r.marker.evaluate({'happypandax':constants.version_str})
                if fail and r.name in markers.VARIABLE:
                    self.unload("'{}{}' failed".format(r.name, str(r.specifier)))
                    unloaded = True
            except (markers.UndefinedComparison, markers.UndefinedEnvironmentName):
                fail = True
            if fail:
                self.info.require.remove(r)
        self._evaluation = not unloaded
        return self._evaluation

    def format(self):
        return format_plugin(self)

class PluginManager:
    ""

    def __init__(self):
        self._event = Event()
        self._node_registry = {} # { pluginid : node }
        self._nodes = set()
        self._commands = {}  # { command : [ plugins ] }
        self._init_plugins_greenlet = async_utils.Greenlet(self._init_plugins)
        self._init_plugins_greenlet.start()

    def _init_plugins(self):

        while True:
            self._event.wait()

            node_items = {}
            for node in self._nodes.copy():
                if node.evaluate():
                    self._collect_dependencies(node)
                    if node.state != PluginState.Unloaded:
                        node_items[node] = list(node.dependencies)
            
            sorted_nodes = []
            for r in reversed(robust_topological_sort(node_items)):
                if len(r) > 1:
                    # circular dependency found
                    pass
                for n in r:
                    if not n in sorted_nodes:
                        sorted_nodes.append(n)

            auto_install = config.auto_install_plugin_dependency.value
            for node in sorted_nodes:
                if node.state == PluginState.Installed:
                    for n in node.dependencies:
                        if n.state == PluginState.Registered:
                            if auto_install:
                                self.install_plugin(n, node)
                            else:
                                node.unload("Required plugin '{}' has not been installed".format(n.info.shortname))
                    if node.state != PluginState.Unloaded:
                        node.init()
                        node.state = PluginState.Enabled

            self._event.clear()

    def get_plugin_logger(self, node_or_id, name):
        node = self.get_node(node_or_id)
        return get_plugin_logger(node.info.shortname+'.'+name, propogate=True)

    def _collect_dependencies(self, node):
        assert isinstance(node, PluginNode)
        for r in node.info.require:
            if r.name in markers.VARIABLE:
                continue
            other_node = self._node_registry.get(r.name)
            ready_version = None
            ready_state = None
            if other_node:
                ready_state = other_node.state not in (PluginState.Unloaded,)
                ready_version = other_node.info.version in r.specifier
                if ready_state and ready_version:
                    node.dependencies.add(other_node)
                    other_node.dependents.add(node)
                    continue
            if ready_state is not None and not ready_state:
                node.unload("Required plugin '{}' is not loaded or has been uninstalled".format(other_node.info.shortname))
            elif ready_version is not None and not ready_version:
                node.unload("Required plugin '{}' does not meet the required version {}".format(other_node.info.shortname, str(r.specifier)))
            else:
                node.unload("Required plugin '{}' is missing and has not been registered".format(r.name))

    def register(self, manifest):
        """
        Registers a plugin

        Returns:
            PluginNode
        """
        assert isinstance(manifest, PluginManifest)
        node = PluginNode(self, manifest)
        pluginid = manifest.id
        if pluginid in self._node_registry:
            raise exceptions.PluginLoadError(
                node, "Plugin ID already exists")
        self._nodes.add(node)
        self._node_registry[pluginid] = node
        self._node_registry.setdefault(node.info.shortname)
        if config.auto_install_plugin.value:
            self.install_plugin(node)
        return node

    def wake_up(self):
        """
        Watches for registered plugins and initiates them
        """
        self._event.set()


    def get_node(self, node_or_id):
        if not isinstance(node_or_id, PluginNode):
            node_or_id = self._node_registry.get(node_or_id)
            if not node_or_id:
                raise exceptions.PluginError("Get plugin", "No plugin with id {} found".format(node_or_id))
        return node_or_id

    def disable_plugin(self, node_or_id):
        "Disable plugin and its dependents"
        node = self.get_node(node_or_id)
        if node.status:
            log.d("Disabling plugin -", node.format(), "\n\tStatus:", node.status)
            node.logger.info("Disabling plugin: {}".format(node.status))
        else:
            log.d("Disabling plugin -", node.format())
            node.logger.info("Disabling plugin")
        node.state = PluginState.Disabled
        for cmd in node.commands:
            if cmd in self._commands:
                if node in self._commands[cmd]:
                    self._commands[cmd].remove(node)

    def install_plugin(self, node_or_id, by_node=None):
        node = self.get_node(node_or_id)
        if by_node is not None:
            log.d("Installing plugin -", node.format(), "by", by_node.format())
            node.logger.info("Installing plugin because '{}' was installed".format(by_node.info.shortname))
        else:
            log.d("Installing plugin -", node.format(), )
            node.logger.info("Installing plugin")
        node.state = PluginState.Installed

    def remove_plugin(self, node_or_id):
        "Remove plugin and its dependents"
        node = self.get_node(node_or_id)
        log.d("Removing plugin -", node.format())
        node.logger.info("Removing plugin")
        self.disable_plugin(node_or_id)
        self._node_registry.pop(node.info.shortname)
        self._node_registry.pop(node.info.id)

        # TODO: disable dependents

    def _call_command(self, command_name, *args, **kwargs):
        """
        Returns HandlerValue
        """
        h = []
        if command_name in self._commands:
            for n in self._commands[command_name]:
                h.append((n, n.commands[command_name]))
        return HandlerValue(command_name, h, *args, **kwargs)

    def attach_to_command(self, node_or_id, command_name, handler):
        ""
        node = self.get_node(node_or_id)
        if command_name not in constants.available_commands:
            raise exceptions.PluginCommandError(
                node, "Command '{}' does not exist".format(command_name))
        if not callable(handler):
            raise exceptions.PluginCommandError(
                node, "Command handler should be callable for command '{}'".format(command_name))

        # TODO: check signature

        node.add_handler(command_name, handler)
        self._commands.setdefault(command_name, []).append(node)

    def subscribe_to_event(self, node_or_id, event_name, handler):
        ""
        raise NotImplementedError
        node = self.get_node(node_or_id)
        if command_name not in constants.available_commands:
            raise exceptions.PluginCommandError(
                node, "Command event '{}' does not exist".format(event_name))
        if not callable(handler):
            raise exceptions.PluginCommandError(
                node, "Command event handler should be callable for command event '{}'".format(event_name))

        # TODO: check signature

        node.add_handler(command_name, handler)
        self._commands.setdefault(command_name, []).append(node)


class HPXImporter(importlib.abc.MetaPathFinder, importlib.abc.Loader):

    def __init__(self, module_spec_cls, modules = {}):
        self._modules = modules
        self._module_spec_cls = module_spec_cls

    def find_spec(self, fullname, path, target=None):
        m_list = ("happypanda",)
        for m in m_list:
            if fullname.startswith(m):
                raise ModuleNotFoundError("No module named '{}'".format(fullname))
        if fullname in self._modules.keys():
            spec = self._module_spec_cls(fullname, self)
            return spec

    def create_module(self, spec):
        return self._modules[spec.name]

    def exec_module(self, module):
        pass

class PluginIsolate:

    base_sys_modules = None

    def __init__(self, node, working_dir=None, do_eggs=True):
        assert isinstance(node, PluginNode)
        # Convert relative paths to absolute paths with parent_dir and
        # evaluate .egg files in the specified directories.
        self.node = node
        path = os.path.abspath(node.info.path)
        self.working_dir = working_dir if working_dir else path
        self.paths = [path]
        if do_eggs:
            self.paths.extend(glob.glob(os.path.join(path, '*.egg')))

        self._old_managers = []
        self._plugin_modules = {}
        self.plugin_globals = {'__name__':'__main__',
                                '__file__': os.path.normpath(os.path.join(path, node.info.entry)),
                                '__doc__': None,
                                '__package__': None,
                                '__spec__': None,
                                '__annotations__': {},
                                '__loader__': None}
        self._sys_modules = {}
        self._sys_metapath = []
        self._sys_path = []
        self._plugin_sys_path = []
        self.in_context = False

        if self.base_sys_modules is None:
            PluginIsolate.base_sys_modules = sys.modules.copy()
            for k in tuple(PluginIsolate.base_sys_modules):
                if k in sys.builtin_module_names:
                    continue
                del PluginIsolate.base_sys_modules[k]

        plug_interface = None
        o_plug_interface = plugins_interface
        del sys.modules[o_plug_interface.__name__]
        try:
            plug_interface = importlib.import_module(o_plug_interface.__name__, o_plug_interface.__package__)
            plug_interface.__plugin_id__ = self.node.info.id
            plug_interface.__manager__ = self.node.manager
        finally:
            sys.modules[o_plug_interface.__name__] = o_plug_interface

        self._hpximporter = HPXImporter(importlib.abc.machinery.ModuleSpec,
                                        {constants.plugin_interface_name: plug_interface})
            

    def _clean_sys_modules(self, sys_modules):
        sys.modules.clear()
        sys.modules.update(self.base_sys_modules)
        sys.modules.update(self._plugin_modules)

    def _clean_sys_path(self, sys_path):
        if self._plugin_sys_path:
            sys.path.clear()
            sys.path.extend(self._plugin_sys_path)
        else:
            for p in reversed(self.paths):
                sys.path.insert(0, p)

        for p in (os.getcwd(),):
            while p in sys.path:
                sys.path.remove(p)

    def __enter__(self):
        self.in_context = True
        log.d("Entering isolation mode for plugin", self.node.format())

        self._sys_metapath = sys.meta_path[:]
        sys.meta_path.insert(0, self._hpximporter)

        self._sys_modules = sys.modules.copy()
        self._clean_sys_modules(sys.modules)

        self._sys_path = sys.path[:]
        self._clean_sys_path(sys.path)

        os.chdir(self.working_dir)

        return self

    def __exit__(self, *_):
        if not self.in_context:
          raise RuntimeError('context not entered')
        self.in_context = False

        self._plugin_modules = sys.modules.copy()
        sys.modules.clear()
        sys.modules.update(self._sys_modules)

        sys.meta_path.clear()
        sys.meta_path.extend(self._sys_metapath)

        self._plugin_sys_path = sys.path.copy()
        sys.path.clear()
        sys.path.extend(self._sys_path)

        os.chdir(self.working_dir)
        log.d("Exiting isolation mode for plugin", self.node.format())

def strongly_connected_components(graph):
    """
    Tarjan's Algorithm (named for its discoverer, Robert Tarjan) is a graph theory algorithm
    for finding the strongly connected components of a graph.

    Based on: http://en.wikipedia.org/wiki/Tarjan%27s_strongly_connected_components_algorithm
    """

    index_counter = [0]
    stack = []
    lowlinks = {}
    index = {}
    result = []

    def strongconnect(node):
        # set the depth index for this node to the smallest unused index
        index[node] = index_counter[0]
        lowlinks[node] = index_counter[0]
        index_counter[0] += 1
        stack.append(node)

        # Consider successors of `node`
        try:
            successors = graph[node]
        except BaseException:
            successors = []
        for successor in successors:
            if successor not in lowlinks:
                # Successor has not yet been visited; recurse on it
                strongconnect(successor)
                lowlinks[node] = min(lowlinks[node], lowlinks[successor])
            elif successor in stack:
                # the successor is in the stack and hence in the current strongly connected component (SCC)
                lowlinks[node] = min(lowlinks[node], index[successor])

        # If `node` is a root node, pop the stack and generate an SCC
        if lowlinks[node] == index[node]:
            connected_component = []

            while True:
                successor = stack.pop()
                connected_component.append(successor)
                if successor == node:
                    break
            component = tuple(connected_component)
            # storing the result
            result.append(component)

    for node in graph:
        if node not in lowlinks:
            strongconnect(node)

    return result

def topological_sort(graph):
    count = {}
    for node in graph:
        count[node] = 0
    for node in graph:
        for successor in graph[node]:
            count[successor] += 1

    ready = [node for node in graph if count[node] == 0]

    result = []
    while ready:
        node = ready.pop(-1)
        result.append(node)

        for successor in graph[node]:
            count[successor] -= 1
            if count[successor] == 0:
                ready.append(successor)

    return result


def robust_topological_sort(graph):
    """ First identify strongly connected components,
        then perform a topological sort on these components. """

    components = strongly_connected_components(graph)

    node_component = {}
    for component in components:
        for node in component:
            node_component[node] = component

    component_graph = {}
    for component in components:
        component_graph[component] = []

    for node in graph:
        node_c = node_component[node]
        for successor in graph[node]:
            successor_c = node_component[successor]
            if node_c != successor_c:
                component_graph[node_c].append(successor_c)

    return topological_sort(component_graph)

