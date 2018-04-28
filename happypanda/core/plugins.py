import os
import uuid
import sys
import importlib
import inspect
import enum
import logging

from gevent.signal import Event

from happypanda.common import exceptions, utils, constants, hlogger

log = hlogger.Logger(constants.log_ns_plugin + __name__)


def format_plugin(node_or_cls):
    ""
    txt = ""
    if isinstance(node_or_cls, PluginNode):
        node_or_cls = node_or_cls.plugin

    if isinstance(node_or_cls, str):
        txt = node_or_cls
    else:
        if hasattr(node_or_cls, "NAME"):
            txt = "{}:{}".format(node_or_cls.SHORTNAME, node_or_cls.ID)
        else:
            txt = "{}".format(node_or_cls.ID)

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
    manifest = None
    for f in os.scandir(path):
        if f.name.lower() == "hplugin.json":
            manifest = f
            break
    if not manifest:
        raise exceptions.CoreError(
            "Plugin loader",
            "No manifest file named 'HPlugin.json' found in plugin directory '{}'".format(path))

    _plugin_load(plug, path, *args, **kwargs)


def _plugin_load(module_name_or_class, path, *args, _logger=None, _manager=None, **kwargs):
    """
    Imports plugin module and registers its main class

    Returns:
        PluginNode
    """
    try:
        sys.path.insert(0, os.path.realpath(path))
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
        if not _logger:
            _logger = get_plugin_logger(cls.NAME, path)
        if not _manager:
            _manager = registered
        return _manager.register(cls, _logger, *args, **kwargs)
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
    log.i('Loading plugins from path:', path)
    for pdir in os.scandir(path):
        plugin_load(pdir.path, *args, **kwargs)
    return registered.init_plugins()


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
            r = handler(*self.args, **self.kwargs)

            if self.expected_type is not None:
                if not isinstance(r, self.expected_type):
                    raise exceptions.PluginHandlerError(
                        "On command '{}' expected type '{}', but got '{}' by plugin handler '{}:{}'".format(
                            self.name, str(type(self.expected_type)), str(type(r)), node.plugin.NAME, node.plugin.ID))

        except Exception as e:

            self.failed[node] = e

            node.logger.exception()

            try:
                if not isinstance(e, exceptions.PluginError):
                    raise exceptions.PluginHandlerError(
                        node, "On command '{}' an unhandled exception was raised by plugin handler '{}:{}'\n\t{}".format(self.name, node.plugin.NAME, node.plugin.ID, e))
                else:
                    raise e
            except exceptions.PluginError:
                log.exception()


class PluginState(enum.Enum):
    Disabled = 0  # puporsely disabled
    Unloaded = 1  # unloaded because of dependencies, etc.
    Init = 2  # was just registered
    Enabled = 3  # plugin is loaded and in use
    Failed = 4  # failed because of error


class PluginNode:
    ""

    def __init__(self, plugin_class, logger, *args, **kwargs):
        self.state = PluginState.Init
        self.plugin = plugin_class
        self.args = args
        self.kwargs = kwargs
        self.depends = {}  # {other_plugin_id : ( ver_start, vers_end )}
        self.commands = {}  # { command : handler }
        self.instanced = None
        self.logger = log if logger is None else logger
        self.load_order = None
        self._list_depends()

    def _list_depends(self):
        ""
        if self.plugin.REQUIRE:
            for x in self.plugin.REQUIRE:
                version_end = (0, 0, 0)
                try:
                    version_end = x[2]
                except IndexError:
                    pass

                self.depends[x[0]] = (x[1], version_end)
            return self.depends

    def formatted(self):
        return format_plugin(self)

    def __eq__(self, other):
        return other == self.plugin.ID

    def __hash__(self):
        return hash(self.plugin.ID)


class PluginManager:
    ""

    def __init__(self):
        self._event = Event()
        self._plugin_registry = {}

        self._nodes = {}
        self._started = False
        self._dirty = False
        self._commands = {}  # { command : [ plugins ] }

    def _dependency_resolver(self):

        while True:
            self._event.wait()
            plugins = set(self._plugin_registry.values())
            plugins_to_load = [x for x in plugins if not x.loaded]
            if plugins_to_load:
                pass


    def register(self, plugin, logger, *args, **kwargs):
        """
        Registers a plugin

        Params:
            - plugin -- main plugin class
            - logger -- plugin logger
            - *args -- additional arguments for plugin
            - **kwargs -- additional keyword arguments for plugin

        Returns:
            PluginNode
        """
        assert isinstance(plugin, HPluginMeta)
        if plugin.ID in self._nodes:
            raise exceptions.PluginError(
                plugin.NAME, "Plugin ID already exists")
        node = PluginNode(plugin, logger, *args, **kwargs)
        self._nodes[plugin.ID] = node
        return node

    def init_plugins(self):
        """
        Instantiate new plugins and (re)solve all dependencies

        Returns a dict with failed plugins: { plugin_id: exception }
        """

        nodes = []

        for plug_id in self._nodes:
            node = self._nodes[plug_id]
            if node.state in (PluginState.Disabled, PluginState.Failed):
                continue

            nodes.append(node)

            #result = self._solve(node, node.depends)
            # if isinstance(result, Exception):
            #    failed[node.plugin.ID] = result
            #    node.state = PluginState.Unloaded
            #    continue

            # if node.state in (PluginState.Init, PluginState.Unloaded):
            #    self._init_plugin(plug_id)

        solved_nodes, failed = self._solve(nodes)

        for node in solved_nodes:
            if not node.state == PluginState.Enabled:
                self._init_plugin(node.plugin.ID)

        return failed

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
                    raise exceptions.PluginError(node, "{}".format(e))
                raise
            node.state = PluginState.Enabled
        else:
            raise exceptions.CoreError(
                utils.this_function(),
                "Plugin node has not been registered with this manager")

    def _ensure_valid_signature(self, node):
        ""
        sig = inspect.signature(node.plugin.__init__)
        pars = list(sig.parameters)
        if not len(pars) == 3:
            raise exceptions.PluginSignatureError(
                node, "Unexpected __init__() signature")
        var_pos = False
        var_key = False
        for a in pars:
            if sig.parameters[a].kind == inspect.Parameter.VAR_POSITIONAL:
                var_pos = True
            elif sig.parameters[a].kind == inspect.Parameter.VAR_KEYWORD:
                var_key = True

        if not (var_pos and var_key):
            raise exceptions.PluginSignatureError(
                node,
                "A __init__ with the following signature must be defined: '__init__(self, *args, **kwargs)'")

    def disable_plugin(self, pluginid):
        "Disable plugin and its dependents"
        node = self._nodes[pluginid]
        node.state = PluginState.Disabled
        for cmd in node.commands:
            if cmd in self._commands:
                if node in self._commands[cmd]:
                    self._commands[cmd].remove(node)

    def remove_plugin(self, plugid):
        "Remove plugin and its dependents"
        self.disable_plugin(plugid)
        self._nodes.pop(plugid)

    def call_command(self, command_name, *args, **kwargs):
        """
        Returns HandlerValue
        """
        h = []
        if command_name in self._commands:
            for n in self._commands[command_name]:
                h.append((n, n.commands[command_name]))
        return HandlerValue(command_name, h, *args, **kwargs)

    def attach_to_command(self, node, command_name, handler):
        ""
        if command_name not in constants.available_commands:
            raise exceptions.PluginCommandError(
                node, "Command '{}' does not exist".format(command_name))
        if not callable(handler):
            raise exceptions.PluginCommandError(
                node, "Handler should be callable for command '{}'".format(command_name))

        # TODO: check signature

        node.commands[command_name] = handler
        if command_name not in self._commands:
            self._commands[command_name] = []
        self._commands[command_name].append(node)

    def _ensure_ready(self, node):
        ""
        assert isinstance(node, PluginNode)
        if not node.state == PluginState.Enabled:
            raise exceptions.PluginError(node, "This plugin is not ready")

    def _ensure_before_init(self, node):
        ""
        assert isinstance(node, PluginNode)
        if not node.state == PluginState.Init:
            raise exceptions.PluginError(
                node, "This method should be called in __init__")


class HPluginMeta(type):

    def __init__(cls, name, bases, dct):
        plugin_requires = ("ID", "NAME", "SHORTNAME", "VERSION", "AUTHOR", "DESCRIPTION")

        for pr in plugin_requires:
            if not hasattr(cls, pr):
                raise exceptions.PluginAttributeError(
                    name, "{} attribute is missing".format(pr))

        for pr in plugin_requires:
            if not getattr(cls, pr):
                raise exceptions.PluginAttributeError(
                    name, "{} attribute cannot be empty".format(pr))

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
        if not isinstance(cls.SHORTNAME, str):
            raise exceptions.PluginAttributeError(
                name, "Plugin shortname should be a string")
        if len(cls.SHORTNAME) > 10:
            raise exceptions.PluginAttributeError(
                name, "Plugin shortname cannot exceed {} characters".format(constants.plugin_shortname_length))
        if not isinstance(cls.VERSION, tuple) or not len(cls.VERSION) == 3:
            raise exceptions.PluginAttributeError(
                name, "Plugin version should be a tuple with 3 integers")
        if not isinstance(cls.AUTHOR, str):
            raise exceptions.PluginAttributeError(
                name, "Plugin author should be a string")
        if not isinstance(cls.DESCRIPTION, str):
            raise exceptions.PluginAttributeError(
                name, "Plugin description should be a string")

        if hasattr(cls, "WEBSITE"):
            if not isinstance(cls.WEBSITE, str):
                raise exceptions.PluginAttributeError(
                    name, "Plugin website should be a string")

        if hasattr(cls, "REQUIRE"):
            e = None

            if cls.REQUIRE:
                # invalid list
                if not isinstance(cls.REQUIRE, (tuple, list)):
                    e = exceptions.PluginAttributeError(
                        cls.NAME, "REQUIRE attribute must be a tuple/list")

                if not e:
                    # wrong list
                    e_x = exceptions.PluginAttributeError(
                        cls.NAME,
                        "REQUIRE should look like this: [ ( ID, (0,0,0), (0,0,0) ) ]")
                    if not all(isinstance(x, (tuple, list)) for x in cls.REQUIRE):
                        e = e_x

                    if not e:
                        e = e_x
                        for x in cls.REQUIRE:
                            if not x:
                                break

                            if len(x) < 2:
                                break

                            if not isinstance(x[0], str):
                                break

                            if not isinstance(x[1], tuple):
                                break

                            try:
                                if not isinstance(x[2], tuple):
                                    break
                            except IndexError:
                                pass
                        else:
                            e = None
            if e:
                raise e
        else:
            cls.REQUIRE = None

        if hasattr(cls, "OPTIONS"):
            pass

        super().__init__(name, bases, dct)

        # set attributes
        attrs = inspect.getmembers(HPluginMeta)

        for n, a in attrs:
            if not n.startswith('_'):
                setattr(cls, n, a)

    def get_logger(cls):
        """
        Return a logger for plugin
        """
        node = registered._nodes.get(cls.ID)
        if not node:
            raise exceptions.PluginIDError(
                cls.NAME, "No plugin found with ID: {}".format(cls.ID))
        return node.logger

    def on_command(cls, command_name, handler, **kwargs):
        """
        Attach handler to command

        Params:
            - command_name -- Name of the Class.command you want to connect to. Eg.: GalleryRename.rename
            - handler -- Your custom method that should be executed when command is invoked
        """
        node = registered._nodes.get(cls.ID)
        if not node:
            raise exceptions.PluginIDError(
                cls.NAME, "No plugin found with ID: {}".format(cls.ID))
        registered._ensure_before_init(node)
        registered.attach_to_command(node, command_name, handler)

    def run_command(cls, command_name, *args, **kwargs):
        """
        Run a command

        Params:
            - command_name -- Name of command you want to run
            - *args and **kwargs sent to command

        Returns command return object
        """
        raise NotImplementedError

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
