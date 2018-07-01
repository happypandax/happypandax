import os
import uuid
import sys
import importlib
import inspect
import gevent
import json
import glob
import logging
import attr
import itertools

from packaging.requirements import Requirement, InvalidRequirement
from packaging.specifiers import Specifier, InvalidSpecifier
from packaging import markers
from packaging.version import Version, InvalidVersion
from gevent.event import Event
from collections import OrderedDict, deque
from logging.handlers import RotatingFileHandler
from contextlib import contextmanager

from happypanda.interface import enums
from happypanda.common import exceptions, constants, hlogger, config, utils
from happypanda.core import plugin_interface, async_utils

log = hlogger.Logger(constants.log_ns_plugin + __name__)

# add hpx marker
markers.VARIABLE |= markers.L("hpx")
markers.VARIABLE |= markers.L("happypandax")
markers.ALIASES['hpx'] = "happypandax"

plugin_logs = {}


def get_plugin_context_logger(logger_name):
    log_name = constants.log_ns_plugin + 'context.' + logger_name[len(constants.log_ns_plugincontext):]
    return plugin_logs.setdefault(log_name, hlogger.Logger(log_name))


@contextmanager
def log_plugin_error(logger, exception=True):
    assert isinstance(logger, logging.Logger) or logger is None
    try:
        yield
    except exceptions.PluginError as e:
        h = logger.exception if exception else logger.error
        h("{}: {}".format(e.__class__.__name__, e.msg))
        get_plugin_context_logger(logger.name).w("{}: '{}' -- {}".format(e.__class__.__name__, e.where, e.msg))


def format_plugin(node):
    ""
    assert isinstance(node, (PluginNode, str))

    txt = ""

    if isinstance(node, str):
        txt = node
    else:
        sid = node.info.id.split('-')
        txt = "{}:{}".format(node.info.shortname, sid[0] + '...' + sid[4])

    return txt


class PluginFilter:
    """
    Reduces error and critical levels to warning
    """

    def filter(self, record):
        if not __file__ == record.pathname:
            levels = {logging.ERROR: logging.WARNING,
                      logging.CRITICAL: logging.WARNING}
            r = logging.LogRecord(
                record.name,
                record.levelno,
                record.pathname,
                record.lineno,
                record.msg,
                record.args,
                record.stack_info)
            r.levelno = levels.get(r.levelno, r.levelno)
            r.levelname = logging.getLevelName(r.levelno)
            l = get_plugin_context_logger(record.name)
            r.name = l.name
            l.handle(r)
        return True


def get_plugin_logger(name, *handler, propogate=False):
    assert name and isinstance(name, str)
    l = logging.getLogger(constants.log_ns_plugincontext + name)
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
    plug_log = get_plugin_logger('loading.' + pname, *log_handlers)
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
                "No manifest file named 'hplugin.json' found in plugin directory '{}'".format(path))
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
            if err:
                raise err
        if not isinstance(manifest, dict):
            raise exceptions.PluginLoadError(pname, "Expected a JSON mapping object")
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
    log.i('Loading plugins from path:', path, stdout=True)
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

                if err:
                    raise err

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

                if err:
                    raise err

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

    def default(self, error=True):
        "Calls the default handler"
        if not self.default_handler:
            return self._raise_default_error() if error else None
        log.d(f"Calling default handler for '{self.name}'")
        r = self.default_handler(*self.args, **self.kwargs)
        return self._ensure_type(r)

    def default_capture(self, token, idx, error=True):
        "Calls the default capture handler"
        log.d(f"Calling default capture handler for '{self.name}' (idx={idx}) [{token}]")
        token_handler_d = self._get_capture_handlers(token, True)

        if token_handler_d:
            r = []
            if idx is not None:
                return self._ensure_type(token_handler_d[0](*self.args, **self.kwargs))
            else:
                for y in token_handler_d:
                    r.append(self._ensure_type(y(*self.args, **self.kwargs)))
            return tuple(r)
        else:
            return self._raise_default_error() if error else None

    def _ensure_type(self, r):
        if self.expected_type is not None:
            if not isinstance(r, self.expected_type):
                raise exceptions.CoreError(
                    utils.this_function(),
                    "Command handler '{}' expected type '{}', but got '{}' by default handler [token={}]".format(
                        self.name, self.expected_type, str(type(r)), self.capture_token))
        return r

    def all(self, default=False):
        "Calls all handlers, returns tuple"
        log.d(f"Calling all handlers (default: {default}) for '{self.name}' [capture={self.capture}]")
        if self.capture:
            r = self._call_capture(None, False, default)
            if r is None:
                return tuple()
            return r
        else:
            r = []
            for n, h in self._handlers:
                with self._unhandled_exception(n):
                    x = self._call_handler(n, h)
                    r.append(x)

            if default and self.default_handler:
                r.append(self.default())

            return tuple(r)

    def all_or_default(self):
        log.d(f"Calling all handlers or default for '{self.name}' [capture={self.capture}]")
        r = self.all()
        if not r:
            if self.capture:
                r = self.default_capture(self.capture_token, None)
            else:
                r = (self.default(),)
        return r

    def get_handlers(self):
        return tuple(x[1] for x in self._handlers)

    def get_node(self, idx):
        return self._handlers[idx][0]

    def first(self):
        "Calls first handler, raises error if there is no handler"
        log.d(f"Calling first handler for '{self.name}'")
        return self._call_node_idx(0, True)

    def first_or_default(self):
        ""
        log.d(f"Calling first handler or default for '{self.name}'")
        return self._call_node_idx(0, True, default=True)

    def first_or_none(self, default=False):
        "Calls first handler, return None if there is no handler"
        log.d(f"Calling first handler or return None for '{self.name}'")
        return self._call_node_idx(0, False, default=default)

    def last(self):
        "Calls last handler, raises error if there is no handler"
        log.d(f"Calling last handler for '{self.name}'")
        return self._call_node_idx(-1, True)

    def last_or_default(self):
        ""
        log.d(f"Calling last handler or default for '{self.name}'")
        return self._call_node_idx(-1, True, default=True)

    def last_or_none(self, default=False):
        "Calls last handler, return None if there is no handler"
        log.d(f"Calling first handler or return None for '{self.name}'")
        return self._call_node_idx(-1, False, default=default)

    def _get_capture_handlers(self, token, default=False):
        if default:
            return self.default_capture_handlers.get(token, [])
        else:
            return self._capture_handlers.get(token, [])

    def _add_capture_handler(self, handler, node=None):
        assert callable(handler)
        assert node is None or isinstance(node, PluginNode)

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
                    if node:
                        log.d(f"Adding capture handler '{handler}' for token '{c}' from plugin", node.format())
                    else:
                        log.d(f"Adding capture handler '{handler}' for token '{c}'")
                    if c not in capture_dict:
                        capture_dict[c] = []

                    if node:
                        capture_dict[c].append((node, handler))
                    else:
                        capture_dict[c].append(handler)

    def _raise_error(self):
        raise exceptions.CoreError(
            self.name + 'handler',
            "No handler is connected to this command: {} (capture token: {})".format(self.name, self.capture_token))

    def _raise_default_error(self):
        raise exceptions.CoreError(
            self.name + 'handler',
            "No default handler is connected to this command: {} (capture token: {})".format(self.name, self.capture_token))

    def _call_capture(self, idx, error, default):
        if not self._capture_handlers and not self.default_capture_handlers:
            if error:
                self._raise_error()
            log.d(
                f"Calling capture handlers but no plugin handlers nor default handlers has been added for '{self.name}'")
            return None

        token_handler = self._get_capture_handlers(self.capture_token)

        token_handler_d = self._get_capture_handlers(self.capture_token, True)

        if not token_handler and not token_handler_d:
            if error:
                self._raise_error()
            log.d(
                f"Calling capture handlers but no plugin handlers nor default handlers has been added for token '{self.capture_token}' in '{self.name}'")
            return None

        r = []

        if token_handler:
            if idx is not None:
                return self._call_handler(*token_handler[idx])
            else:
                for y in token_handler:
                    with self._unhandled_exception(y[0]) as err:  # noqa: F841
                        r.append(self._call_handler(*y))

        if token_handler_d and default:
            if idx is not None:
                return token_handler_d[0](*self.args, **self.kwargs)
            else:
                for y in token_handler_d:
                    r.append(y(*self.args, **self.kwargs))
        elif not token_handler and error and default:
            self._raise_default_error()

        return tuple(x for x in r if x is not None)

    def _call_node_idx(self, idx, error=False, until_result=True, default=False):
        handlers = []
        if self.capture:
            handlers = self._get_capture_handlers(self.capture_token)
        else:
            handlers = self._handlers

        # traverse all items in a list from any idx, e.g: [0, 1, 2, 3] -> (from 2) [2, 3, 0, 1]
        # does not work with negative indexes
        if handlers:
            handlers_idx_list = list(range(len(handlers)))
            idx = handlers_idx_list[idx] if idx < 0 else idx
            handlers_idx = list(itertools.islice(itertools.cycle(handlers_idx_list), len(handlers) * 2))
            handlers_idx = handlers_idx[idx:-1 * len(handlers) + idx]
        else:
            handlers_idx = handlers_idx = (idx,)
        for i in handlers_idx:
            with self._unhandled_exception(handlers[i][0] if i <= len(handlers) - 1 else None) as err:
                u_err = err
                if self.capture:
                    return self._call_capture(i, error, default)
                else:
                    if not self._handlers and default:
                        return self.default(error)
                    elif not self._handlers and error:
                        self._raise_error()
                    elif not self._handlers:
                        return None
                    return self._call_handler(*self._handlers[i])
            if until_result and u_err.raised_error:
                continue
            break

    @contextmanager
    def _unhandled_exception(self, node):
        assert isinstance(node, PluginNode) or node is None

        @attr.s
        class ErrorInfo:
            raised_error = attr.ib(False)
            exception = attr.ib(None)

        err_info = ErrorInfo()

        try:
            yield err_info
        except Exception as e:
            if node is None or (isinstance(e, exceptions.CoreError) and e.where == self.name + 'handler'):
                raise
            if node:
                self.failed[node] = e
                node.logger.exception(
                    f"An unhandled exception '{e.__class__.__name__}' was raised by plugin handler on command '{self.name}'".format(
                        self.name))
                get_plugin_context_logger(
                    node.logger.name).w(
                    f"An unhandled exception '{e.__class__.__name__}' was raised by plugin handler on command '{self.name}' by",
                    node.format())

            err_info.raised_error = True
            err_info.exception = e

    def _call_handler(self, node, handler):
        r = node.call_handler(self.name, handler, self.args, self.kwargs)

        if self.expected_type is not None:
            if not isinstance(r, self.expected_type):
                raise exceptions.PluginHandlerError(
                    node,
                    "Command handler '{}' expected type '{}', but got '{}' by plugin '{}'".format(
                        self.name, self.expected_type, str(type(r)), node.format()))
        return r


class PluginNode:
    ""

    def __init__(self, manager, manifest):
        self.state = enums.PluginState.Registered
        self.manager = manager
        self.info = manifest
        self.commands = {'event': {}, 'entry': {}}  # { command : handler }
        self._modules = []
        self._isolate = None
        self.dependencies = set()
        self.dependents = set()
        self._evaluation = None
        self.status = ""
        self.logger = get_plugin_logger(self.info.shortname, *create_plugin_logger(self.info.path))
        self._special_handlers = {}

    def init(self):
        log.i("Initiating plugin -", self.format())
        self.logger.info("Initiating plugin")
        self._isolate = PluginIsolate(self)
        err = None
        entry_file = os.path.splitext(self.info.entry)[0]
        try:
            with self._isolate as i:
                exec(f"import {entry_file}", i.plugin_globals)
        except Exception as e:
            err = e
            self.logger.exception(
                f"An unhandled exception '{e.__class__.__name__}' was raised during plugin initialization")
            get_plugin_context_logger(self.logger.name).w(
                "An unhandled exception was raised during plugin initialization by {}: {}: {}".format(self.format(), e.__class__.__name__, str(e)))

        return False if err else True

    def add_handler(self, command, handler):
        log.d("Adding command handler to", command, "-", self.format())
        self.logger.info("Adding command handler to '{}'".format(command))
        self.commands['entry'][command] = handler

    def add_event_handler(self, command, handler):
        log.d("Adding command event handler to", command, "-", self.format())
        self.logger.info("Adding command event handler to '{}'".format(command))
        if command in self.special_events():
            self._special_handlers[command] = handler
        else:
            self.commands['event'][command] = handler

    def call_handler(self, commandname, handler, args, kwargs):
        log.d("Calling command handler for '{}' -".format(commandname), self.format())
        self.logger.info("Calling command handler for '{}'".format(commandname))
        with self._isolate:
            return handler(*args, *kwargs)

    def call_special_handler(self, event_name):
        assert event_name in self.special_events()
        handler = self._special_handlers.get(event_name)
        if handler:
            log.d("Calling handler for '{}' -".format(event_name), self.format())
            self.logger.info("Calling '{}' handler".format(event_name))
            try:
                with self._isolate:
                    handler()
            except Exception as e:
                self.logger.exception(
                    f"An unhandled exception '{e.__class__.__name__}' was raised in the plugin '{event_name}' handler")
                get_plugin_context_logger(self.logger.name).w(
                    "An unhandled exception was raised in the '{}' handler by plugin {}: {}: {}".format(event_name, self.format(), e.__class__.__name__, str(e)))

    def update_state(self, state):
        assert isinstance(state, enums.PluginState)
        self.state = state
        ps = constants.internaldb.plugins_state.get({})
        ps[self.info.id] = self.state.value
        constants.internaldb.plugins_state.set(ps)
        if state == enums.PluginState.Disabled:
            self.call_special_handler("disable")

    def unload(self, reason=""):
        if self.state == enums.PluginState.Unloaded:
            return
        log.d("Unloading plugin -", self.format())
        self.logger.info("Unloading plugin")
        self.status = reason
        self.manager.disable_plugin(self)
        self.update_state(enums.PluginState.Unloaded)
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
                    fail = not r.marker.evaluate({'happypandax': constants.version_str})
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

    @classmethod
    def special_events(cls):
        return ("init", "remove", "disable")


class PluginManager:
    ""

    def __init__(self):
        self._event = Event()
        self._node_registry = {}  # { pluginid : node }
        self._nodes = set()
        self._commands = {'entry': {}, 'event': {}}  # { command : set( plugins ) }
        self._init_plugins_greenlet = async_utils.Greenlet(self._init_plugins)
        self._init_plugins_greenlet.start()

    def _init_plugins(self):

        while True:
            self._event.wait()

            node_items = {}
            for node in self._nodes.copy():
                if node.evaluate():
                    self._collect_dependencies(node)
                    if node.state != enums.PluginState.Unloaded:
                        node_items[node] = list(node.dependencies)

            sorted_nodes = []
            for r in reversed(robust_topological_sort(node_items)):
                if len(r) > 1:
                    # circular dependency found
                    log.w("Circular dependency found between", *[n.info.shortname + ',' for n in r])

                for n in r:
                    if n not in sorted_nodes:
                        sorted_nodes.append(n)

            enabled_nodes = []
            auto_install = config.auto_install_plugin_dependency.value
            for node in sorted_nodes:
                if node.state == enums.PluginState.Installed:
                    for n in node.dependencies:
                        if n.state == enums.PluginState.Registered:
                            if auto_install:
                                self.install_plugin(n, node, wake_up=False)
                            else:
                                node.unload("Required plugin '{}' has not been installed".format(n.info.shortname))
                    if node.state != enums.PluginState.Unloaded:
                        node.init()
                        node.update_state(enums.PluginState.Enabled)
                        enabled_nodes.append(node)

            for node in enabled_nodes:
                node.call_special_handler("init")
            self._event.clear()

    def _collect_dependencies(self, node):
        assert isinstance(node, PluginNode)
        for r in node.info.require:
            if r.name in markers.VARIABLE:
                continue
            other_node = self._node_registry.get(r.name)
            ready_version = None
            ready_state = None
            if other_node:
                ready_state = other_node.state not in (enums.PluginState.Unloaded,)
                ready_version = other_node.info.version in r.specifier
                if ready_state and ready_version:
                    node.dependencies.add(other_node)
                    other_node.dependents.add(node)
                    continue
            if ready_state is not None and not ready_state:
                node.unload(
                    "Required plugin '{}' is not loaded or has been uninstalled".format(
                        other_node.info.shortname))
            elif ready_version is not None and not ready_version:
                node.unload(
                    "Required plugin '{}' does not meet the required version {}".format(
                        other_node.info.shortname, str(
                            r.specifier)))
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
        saved_state = constants.internaldb.plugins_state.get({}).get(node.info.id)
        if saved_state == enums.PluginState.Disabled:
            self.disable_plugin(node)
        elif config.auto_install_plugin.value or saved_state not in (None, enums.PluginState.Registered):
            self.install_plugin(node, wake_up=False)
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
        node.update_state(enums.PluginState.Disabled)
        for n, cmd_dict in node.commands.items():
            for cmd in cmd_dict:
                if cmd in self._commands[n]:
                    if node in self._commands[n][cmd]:
                        self._commands[n][cmd].remove(node)

    def install_plugin(self, node_or_id, by_node=None, wake_up=True):
        node = self.get_node(node_or_id)
        if by_node is not None:
            log.d("Installing plugin -", node.format(), "by", by_node.format())
            node.logger.info("Installing plugin because '{}' was installed".format(by_node.info.shortname))
        else:
            log.d("Installing plugin -", node.format(), )
            node.logger.info("Installing plugin")
        node.update_state(enums.PluginState.Installed)
        if wake_up:
            self.wake_up()

    def remove_plugin(self, node_or_id):
        "Remove plugin and its dependents"
        node = self.get_node(node_or_id)
        log.d("Removing plugin -", node.format())
        node.logger.info("Removing plugin")
        self.disable_plugin(node_or_id)
        self._node_registry.pop(node.info.shortname)
        self._node_registry.pop(node.info.id)
        node.call_special_handler("remove")

        # TODO: disable dependents

    def _call_command_entry(self, command_name, *args, **kwargs):
        """
        Returns HandlerValue
        """
        h = []
        if command_name in self._commands['entry']:
            for n in self._commands['entry'][command_name]:
                h.append((n, n.commands['entry'][command_name]))
        return HandlerValue(command_name, h, *args, **kwargs)

    def _call_command_event(self, command_name, *args, **kwargs):
        """
        """
        h = []
        if command_name in self._commands['event']:
            for n in self._commands['event'][command_name]:
                h.append((n, n.commands['event'][command_name]))

        return HandlerValue(command_name, h, *args, **kwargs).all(default=True)

    def attach_to_command(self, node_or_id, command_name, handler):
        ""
        node = self.get_node(node_or_id)
        log.d("Attaching plugin handler to entry '{}' -".format(command_name), node.format())
        node.logger.debug("Attaching handler to entry '{}'".format(command_name))
        if command_name not in constants.available_commands['entry']:
            raise exceptions.PluginCommandError(
                node, "Command '{}' does not exist".format(command_name))
        if not callable(handler):
            raise exceptions.PluginCommandError(
                node, "Command handler should be callable for command '{}'".format(command_name))

        # TODO: check signature

        node.add_handler(command_name, handler)
        self._commands['entry'].setdefault(command_name, set()).add(node)

    def subscribe_to_event(self, node_or_id, event_name, handler):
        ""
        node = self.get_node(node_or_id)
        log.d("Subscribing plugin handler to event '{}' -".format(event_name), node.format())
        node.logger.debug("Subscribing handler to event '{}'".format(event_name))

        if event_name in constants.available_commands['event'] or event_name in PluginNode.special_events():

            if not callable(handler):
                raise exceptions.PluginCommandError(
                    node, "Command event handler should be callable for command event '{}'".format(event_name))

            # TODO: check signature

            node.add_event_handler(event_name, handler)
            if event_name not in PluginNode.special_events():
                self._commands['event'].setdefault(event_name, set()).add(node)

        else:
            raise exceptions.PluginCommandError(
                node, "Command event '{}' does not exist".format(event_name))

    def get_plugin_logger(self, node_or_id, name):
        node = self.get_node(node_or_id)
        log.d("Getting plugin logger -", node.format())
        node.logger.debug("Getting logger")
        logname = node.info.shortname
        propogate = False
        if name:
            logname += '.' + name
            propogate = True
        return get_plugin_logger(logname, propogate=propogate)

    def _plugin_config_key(self, node_or_id):
        node = self.get_node(node_or_id)
        return node.info.shortname + '.' + node.info.id.split('-')[1]

    def get_plugin_config(self, node_or_id):
        node = self.get_node(node_or_id)
        log.d("Getting plugin configuration -", node.format())
        node.logger.debug("Getting configuration")
        return PluginConfig(config.config.get(config.plugin_ns, self._plugin_config_key(node), {}))

    def get_setting(self, node_or_id, ns, key):
        node = self.get_node(node_or_id)
        log.d("Getting setting -", node.format())
        node.logger.debug("Getting setting")
        return config.config.get(ns, key)

    def save_plugin_config(self, node_or_id, dictlike):
        node = self.get_node(node_or_id)
        log.d("Saving plugin configuration -", node.format())
        node.logger.debug("Saving configuration")
        with config.config.namespace(config.plugin_ns):
            config.config.update(self._plugin_config_key(node), dictlike, create=True)
        return config.config.save()


class PluginConfig(dict):
    pass


@attr.s(frozen=True)
class PluginConstants:
    """
    - version: current HPX version
    - database_version: current HPX database version
    - webclient_version: current HPX webclient version
    - dev: developer mode enabled
    - dev: debug mode enabled
    - is_frozen: application has been made into an executable
    - is_osx: application is running on OS X
    - is_linux: application is running on Linux
    - is_win: application is running on Windows
    - is_posix: application is running on a posix-compliant OS (true for both OS X and Linux)
    - download_path: path to the downloads folder
    - tumbnail_path: path to the thumbnails folder
    - translation_path: path to the translations folder
    - current_dir: path to the plugin's folder
    """
    version = attr.ib(constants.version)
    database_version = attr.ib(constants.version_db)
    webclient_version = attr.ib(constants.version_web)
    dev = attr.ib(constants.dev)
    debug = attr.ib(config.debug.value)
    is_frozen = attr.ib(constants.is_frozen)
    is_osx = attr.ib(constants.is_osx)
    is_win = attr.ib(constants.is_win)
    is_linux = attr.ib(constants.is_linux)
    is_posix = attr.ib(constants.is_posix)
    download_path = attr.ib(constants.dir_download)
    thumbnail_path = attr.ib(constants.dir_thumbs)
    translation_path = attr.ib(constants.dir_translations)
    current_dir = attr.ib("")


class PluginCommands:

    def __init__(self, node_id):
        self.__node_id = node_id

    def __getattr__(self, attr):
        node = constants.plugin_manager.get_node(self.__node_id)
        get_plugin_context_logger(node.info.shortname).d(f"Getting command '{attr}' -", node.format())
        node.logger.debug(f"Getting command '{attr}'")
        cmd_cls = constants.available_commands['class'].get(attr)
        if not cmd_cls:
            raise exceptions.PluginCommandNotFoundError(node, f"Invalid command name '{attr}'")

        class PluginCommand:
            def __init__(self):
                self.__cmd = None

            def __call__(self, *args, **kwargs):
                get_plugin_context_logger(node.info.shortname).d(f"Initiating command '{attr}' -", node.format())
                node.logger.debug(f"Initiating command '{attr}'")
                main_func = getattr(cmd_cls, 'main', False)
                if main_func:
                    cmd = cmd_cls()
                    return cmd.main(*args, **kwargs)
                else:
                    cmd = cmd_cls(*args, **kwargs)
                self.__cmd = cmd
                return self

            def __repr__(self):
                if self.__cmd:
                    return self.__cmd.__repr__()
                return super().__repr__()

            def __str__(self):
                if self.__cmd:
                    return self.__cmd.__str__()
                return super().__str__()

            def __getattr__(self, cmd_attr):
                if self.__cmd:
                    if not cmd_attr.startswith('_'):
                        return getattr(self.__cmd, cmd_attr)
                raise AttributeError(f"AttributeError: '{attr}' object has no attribute '{cmd_attr}'")

        return PluginCommand()


class HPXImporter(importlib.abc.MetaPathFinder, importlib.abc.Loader):

    def __init__(self, module_spec_cls, modules={}):
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
        self.plugin_globals = {'__name__': '__main__',
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
        self._in_context = deque()

        if self.base_sys_modules is None:
            PluginIsolate.base_sys_modules = sys.modules.copy()
            for k in tuple(PluginIsolate.base_sys_modules):
                if k.startswith('happypanda'):
                    del PluginIsolate.base_sys_modules[k]

        plug_interface = None
        o_plug_interface = plugin_interface
        del sys.modules[o_plug_interface.__name__]
        try:
            plug_interface = importlib.import_module(o_plug_interface.__name__, o_plug_interface.__package__)
            plug_interface.__plugin_id__ = self.node.info.id
            plug_interface.__manager__ = self.node.manager
            plug_interface.__package__ = constants.plugin_interface_name
            plug_interface.constants = PluginConstants(current_dir=self.working_dir)
            plug_interface.command = PluginCommands(node.info.id)
        finally:
            sys.modules[o_plug_interface.__name__] = o_plug_interface

        for name, obj in inspect.getmembers(exceptions, inspect.isclass):
            if issubclass(obj, Exception):
                setattr(plug_interface, name, obj)

        for name, obj in inspect.getmembers(enums, inspect.isclass):
            if issubclass(obj, enums._APIEnum):
                setattr(plug_interface, name, obj)

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
        self._in_context.append(True)
        log.d("Entering isolation mode for plugin", self.node.format())

        self._sys_metapath = sys.meta_path[:]
        sys.meta_path.insert(0, self._hpximporter)

        self._sys_modules = sys.modules.copy()
        self._clean_sys_modules(sys.modules)

        self._sys_path = sys.path[:]
        self._clean_sys_path(sys.path)

        return self

    def __exit__(self, *_):
        try:
            self._in_context.pop()
        except IndexError:
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
