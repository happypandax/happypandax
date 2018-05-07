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

from gevent.event import Event
from collections import OrderedDict

from happypanda.interface.enums import PluginState
from happypanda.common import exceptions, utils, constants, hlogger, config
from happypanda.core import plugins_interface, async_utils

log = hlogger.Logger(constants.log_ns_plugin + __name__)

def format_plugin(node):
    ""
    assert isinstance(node, (PluginNode, str))

    txt = ""

    if isinstance(node, str):
        txt = node
    else:
        txt = "{}:{}".format(node.info.shortname, node.info.id)

    return txt


def get_plugin_logger(plugin_name, plugin_dir):
    "Create a logger for plugin"
    file_name = os.path.join(plugin_dir, "plugin.log")
    file_mode = "a"
    file_enc = 'utf-8'

    try:
        with open(file_name, 'x', encoding=file_enc) as f:  # noqa: F841
            pass
    except FileExistsError:
        pass

    l = hlogger.Logger('HPX Plugin.' + plugin_name)
    l._logger.propagate = False
    l._logger.setLevel(logging.INFO)
    fhandler = logging.FileHandler(file_name, file_mode, file_enc)
    l._logger.addHandler(fhandler)
    return l


def plugin_load(plugin_manager, path, *args, **kwargs):
    """
    Attempts to load a plugin

    Params:
        - path -- path to plugin directory
        - *args -- additional arguments for plugin
        - **kwargs -- additional keyword arguments for plugin
    """
    manifest = None
    for f in os.scandir(path):
        if f.name.lower() == "hplugin.json":
            manifest = f.path
            break
    if not manifest:
        raise exceptions.PluginLoadError(
            "Plugin loader",
            "No manifest file named 'HPlugin.json' found in plugin directory '{}'".format(path))

    _plugin_load(plugin_manager, manifest, path, *args, **kwargs)


def _plugin_load(plugin_manager, manifest, path, *args, _logger=None, **kwargs):
    """
    Imports plugin module and registers its main class

    Returns:
        manifest dict
    """
    assert isinstance(manifest, str)
    with open(manifest, 'r', encoding='utf-8') as f:
        manifest = json.load(f)
    pentry = manifest.get("entry")
    if pentry:
        if not os.path.exists(os.path.join(path, pentry)):
            raise exceptions.PluginLoadError("Plugin loader", "Plugin entry {} does not exist".format(pentry))
    ptest = manifest.get("test")
    if ptest:
        if not os.path.exists(os.path.join(path, ptest)):
            raise exceptions.PluginLoadError("Plugin loader", "Plugin test {} does not exist".format(ptest))
    manifestobj = PluginManifest(manifest, path)
    return plugin_manager.register(manifestobj, _logger, *args, **kwargs)


def plugin_loader(plugin_manager, path, *args, **kwargs):
    """
    Scans provided paths for viable plugins and attempts to load them

    Params:
        - path -- path to directory of plugins
        - *args -- additional arguments for plugin
        - **kwargs -- additional keyword arguments for plugin

    """
    assert isinstance(plugin_manager, PluginManager)
    log.i('Loading plugins from path:', path)
    plugindirs = list(os.scandir(path))
    log.i("Loading", len(plugindirs), "plugins", stdout=True)
    for pdir in plugindirs:
        gevent.spawn(plugin_load, plugin_manager, pdir.path, *args, **kwargs).join()
    plugin_manager.wake_up()

class PluginManifest(OrderedDict):

    def __init__(self, manifest, path=""):
        assert isinstance(manifest, dict)
        manifest['path'] = path
        name = "Plugin loader"
        plugin_requires = ("id", "entry", "name", "shortname", "version", "author", "description")

        for pr in plugin_requires:
            if not manifest.get(pr):
                raise exceptions.PluginAttributeError(
                    name, "{} attribute is missing".format(pr))

        for pr in plugin_requires:
            if not manifest.get(pr):
                raise exceptions.PluginAttributeError(
                    name, "{} attribute cannot be empty".format(pr))

        try:
            uid = manifest.get("id").replace('-', '')
            val = uuid.UUID(uid, version=4)
            assert val.hex == uid
        except ValueError:
            raise exceptions.PluginIDError(
                name, "Invalid plugin id. UUID4 is required.")
        except AssertionError:
            raise exceptions.PluginIDError(
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
        #if not isinstance(cls.VERSION, tuple) or not len(cls.VERSION) == 3:
        #    raise exceptions.PluginAttributeError(
        #        name, "Plugin version should be a tuple with 3 integers")
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
                    name, "Plugin website should be a filename")

        #if manifest.get('require'):
        #    e = None

        #    if cls.REQUIRE:
        #        # invalid list
        #        if not isinstance(cls.REQUIRE, (tuple, list)):
        #            e = exceptions.PluginAttributeError(
        #                cls.NAME, "REQUIRE attribute must be a tuple/list")

        #        if not e:
        #            # wrong list
        #            e_x = exceptions.PluginAttributeError(
        #                cls.NAME,
        #                "REQUIRE should look like this: [ ( ID, (0,0,0), (0,0,0) ) ]")
        #            if not all(isinstance(x, (tuple, list)) for x in cls.REQUIRE):
        #                e = e_x

        #            if not e:
        #                e = e_x
        #                for x in cls.REQUIRE:
        #                    if not x:
        #                        break

        #                    if len(x) < 2:
        #                        break

        #                    if not isinstance(x[0], str):
        #                        break

        #                    if not isinstance(x[1], tuple):
        #                        break

        #                    try:
        #                        if not isinstance(x[2], tuple):
        #                            break
        #                    except IndexError:
        #                        pass
        #                else:
        #                    e = None
        #    if e:
        #        raise e
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
        try:
            r = node.call_handler(handler, self.args, self.kwargs)

            if self.expected_type is not None:
                if not isinstance(r, self.expected_type):
                    raise exceptions.PluginHandlerError(
                        "On command '{}' expected type '{}', but got '{}' by plugin handler '{}'".format(
                            self.name, str(type(self.expected_type)), str(type(r)), node.format()))

        except Exception as e:

            self.failed[node] = e

            node.logger.exception()

            try:
                if not isinstance(e, exceptions.PluginError):
                    raise exceptions.PluginHandlerError(
                        node, "On command '{}' an unhandled exception was raised by plugin handler '{}'\n\t{}".format(self.name, node.format(), e))
                else:
                    raise e
            except exceptions.PluginError:
                log.exception()

class PluginNode:
    ""

    def __init__(self, manager, manifest, logger, *args, **kwargs):
        self.state = PluginState.Registered
        self.manager = manager
        self.info = manifest
        self.args = args
        self.kwargs = kwargs
        self.commands = {}  # { command : handler }
        self._modules = []
        self.logger = log if logger is None else logger
        self._isolate = None
        self.dependencies = []
        self.dependents = []

    def init(self):
        log.i("Initiating plugin -", self.format())
        self._isolate = PluginIsolate(self)
        with open(os.path.join(self.info.path, self.info.entry)) as f:
            with self._isolate:
                exec(f.read(), globals())

    def add_handler(self, command, handler):
        log.d("Adding command handler to", command, "-", self.format())
        self.commands[command] = handler

    def call_handler(self, handler, args, kwargs):
        log.d("Calling command handler by", self.format())
        with self._isolate:
            return handler(*args, *kwargs)

    def format(self):
        return format_plugin(self)

    def __eq__(self, other):
        if isinstance(other, PluginNode):
            return other == self.info.id
        return super.__eq__(other)

    def __hash__(self):
        return hash(self.info.ID)


class PluginManager:
    ""

    def __init__(self):
        self._event = Event()
        self._nodes = {} # { pluginid : node }
        self._commands = {}  # { command : [ plugins ] }
        self._init_plugins_greenlet = async_utils.Greenlet(self._init_plugins)
        self._init_plugins_greenlet.start()

    def _init_plugins(self):

        while True:
            self._event.wait()

            # TODO: solve plugin dependecies
            node_items = self._nodes.items()

            # TODO: auto install plugin dependecies

            for plugid, node in node_items:
                if node.state == PluginState.Installed:
                    node.init()
                    node.state = PluginState.Enabled

            self._event.clear()

    def register(self, manifest, logger, *args, **kwargs):
        """
        Registers a plugin

        Params:
            - logger -- plugin logger
            - *args -- additional arguments for plugin
            - **kwargs -- additional keyword arguments for plugin

        Returns:
            PluginNode
        """
        assert isinstance(manifest, PluginManifest)
        pluginid = manifest.id
        if pluginid in self._nodes:
            raise exceptions.PluginError(
                manifest.name, "Plugin ID already exists")
        node = PluginNode(self, manifest, logger, *args, **kwargs)
        self._nodes[pluginid] = node
        if config.auto_install_plugin.value:
            self.install_plugin(node)
        return node

    def wake_up(self):
        """
        Watches for registered plugins and initiates them
        """
        self._event.set()


    def _solve(self, nodes):
        """
        Returns a tuple of:
            - An ordered list of node, in the order they should be initiated in
            - Nodes that failed the dependency resolving {node:exception}
        """
        failed = {}

        universal = []
        inverse = []
        provides = {}

        # solve hard requirements
        for node in nodes:
            for otherpluginid in node.depends:
                formatted = format_plugin(otherpluginid)
                # check if required plugin is present
                e = None
                if otherpluginid in self._nodes:
                    if self._nodes[otherpluginid].state == PluginState.Unloaded:
                        e = exceptions.PluginError(
                            node, "A required plugin failed to load: {}".format(formatted))
                    elif self._nodes[otherpluginid].state == PluginState.Disabled:
                        e = exceptions.PluginError(
                            node,
                            "A required plugin has been disabled: {}".format(formatted))
                else:
                    e = exceptions.PluginError(
                        node, "A required plugin is not present: {}".format(formatted))

                if not e:
                    vers = node.depends[otherpluginid]
                    other_node = self._nodes[otherpluginid]
                    # compare versions
                    other_version = other_node.plugin.VERSION
                    if not vers[0] <= other_version:
                        e = exceptions.PluginError(
                            node,
                            "A required plugin does not meet version requirement {} <= {}: {}".format(
                                vers[0],
                                other_version,
                                formatted))
                    if not vers[1] == (0, 0, 0) and not vers[1] > other_version:
                        e = exceptions.PluginError(
                            node,
                            "A required plugin does not meet version requirement {} > {}: {}".format(
                                vers[1],
                                other_version,
                                formatted))
                if e:
                    failed[node] = e
                    break
            else:
                provides[node.plugin.ID] = node
                provides[node.plugin.SHORTNAME] = node

                if node.load_order == "first":
                    universal.append(node)
                elif node.load_order == "last":
                    inverse.append(node)

        # build initial graph

        dependencies = {}

        for node in nodes:

            reqs = set(node.depends.keys())
            dependencies[node] = set(provides[x] for x in reqs)

            if universal and node not in universal:
                dependencies[node].update(universal)

            if inverse and node in inverse:
                dependencies[node].update(set(nodes).difference(inverse))

        # solver
        dependencies = robust_topological_sort(dependencies)

        node_order = []
        for node in dependencies:
            # circular reference
            if len(node) > 1:
                for n in node:
                    failed[n] = exceptions.PluginError("Circular dependency found: {}".format(node))
                continue

            node_order.append(node[0])

        node_order.reverse()

        return node_order, failed

    def get_node(self, node_or_id):
        if not isinstance(node_or_id, PluginNode):
            node_or_id = self._nodes.get(node_or_id)
            if not node_or_id:
                raise exceptions.PluginError("Get plugin", "No plugin with id {} found".format(node_or_id))
        return node_or_id

    def disable_plugin(self, node_or_id):
        "Disable plugin and its dependents"
        node = self.get_node(node_or_id)
        log.d("Disabling plugin -", node.format())
        node.state = PluginState.Disabled
        for cmd in node.commands:
            if cmd in self._commands:
                if node in self._commands[cmd]:
                    self._commands[cmd].remove(node)

        # TODO: disable dependents?

    def install_plugin(self, node_or_id):
        node = self.get_node(node_or_id)
        log.d("Installing plugin -", node.format())
        node.state = PluginState.Installed

    def remove_plugin(self, node_or_id):
        "Remove plugin and its dependents"
        node = self.get_node(node_or_id)
        log.d("Removing plugin -", node.format())
        self.disable_plugin(node_or_id)
        self._nodes.pop(node.info.id)

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

    def subscribe_to_command(self, node_or_id, command_name, handler):
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

    _base_sys_modules = None

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
        self._globals = {}
        self._locals = {}
        self._plugin_globals = {'__name__':'__main__',
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

        if self._base_sys_modules is None:
            PluginIsolate._base_sys_modules = sys.modules.copy()
            for k in tuple(PluginIsolate._base_sys_modules):
                if k in sys.builtin_module_names:
                    continue
                del PluginIsolate._base_sys_modules[k]

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
        sys.modules.update(self._base_sys_modules)
        sys.modules.update(self._plugin_modules)

    def _clean_sys_path(self, sys_path):
        if self._plugin_sys_path:
            sys.path.clear()
            sys.path.extend(self._plugin_sys_path)
        else:
            for p in reversed(self.paths):
                sys.path.insert(0, p)

        for p in (os.getcwd(),):
            print(p)
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

        self._globals = globals().copy()
        self._locals = locals().copy()

        os.chdir(self.working_dir)

        globals().clear()
        locals().clear()

        globals().update(self._plugin_globals)
        locals().update(self._plugin_globals)

        return self

    def __exit__(self, *_):
        if not self.in_context:
          raise RuntimeError('context not entered')
        self.in_context = False

        self._plugin_globals = globals().copy()
        globals().clear()
        globals().update(self._globals)

        locals().clear()
        locals().update(self._locals)

        # ----------------------------------

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
