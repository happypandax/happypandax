import os
import pickle
import base64
import yaml

from contextlib import contextmanager
from collections import ChainMap, OrderedDict

from happypanda.common import exceptions, hlogger, constants

log = hlogger.Logger(__name__)

class ConfigNode:

    def __init__(self, cfg, ns, name, value, description="", type_=None):
        self._cfg = cfg
        self.namespace = ns
        self.name = name
        self.default = self._value = value
        self.description = description
        self.type_ = type_
        self._created = False
        with self._cfg.namespace(ns):
            self._cfg.define(name, value, description)

    @property
    def value(self):
        self._create()
        return self._value

    @value.setter
    def value(self, new_value):
        self._create()
        self._value = new_value

    def _create(self):
        if not self._created:
            self._cfg.get(self.namespace, self.name, default=self._value, create=False, description=self.description, type_=self.type_)
            self._created = True

    def __bool__(self):
        self._create()
        return bool(self.value)

class Config:

    def __init__(self, *filepaths):
        self._cfg = OrderedDict()
        self._current_ns = None
        self._files = filepaths
        self._files_map = {}
        self._comments = {}
        self._default_config = OrderedDict()
        self._loaded = False
        self._cmd_args_applied = False
        self._tmp_context = False

    def create(self, ns, key, default=None, description="", type_=None):
        return ConfigNode(self, ns, key, default, description, type_)

    
    def _ordered_load(self, stream, Loader=yaml.SafeLoader, object_pairs_hook=OrderedDict):
        class OrderedLoader(Loader):
            pass
        def construct_mapping(loader, node):
            loader.flatten_mapping(node)
            return object_pairs_hook(loader.construct_pairs(node))
        OrderedLoader.add_constructor(
            yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
            construct_mapping)
        return yaml.load(stream, OrderedLoader)

    def _ordered_dump(self, data, stream=None, Dumper=yaml.SafeDumper, **kwds):
        class OrderedDumper(Dumper):
            pass
        def _dict_representer(dumper, data):
            return dumper.represent_mapping(
                yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
                data.items())
        OrderedDumper.add_representer(OrderedDict, _dict_representer)
        return yaml.dump(data, stream, OrderedDumper, **kwds)

    def load(self):
        for f in self._files:
            if os.path.exists(f):
                log.i("Loading existing configuration from", os.path.abspath(f))
                with open(f, 'r', encoding='utf-8') as rf:
                    f_dict = self._ordered_load(rf)
                if not isinstance(f_dict, dict):
                    log.w("Invalid or empty configuration file, expected mapping")
                    f_dict = OrderedDict()
                self._files_map[f] = f_dict
                for ns in f_dict:
                    ns_dict = f_dict[ns]
                    ns = self._get_namespace(ns)
                    if not isinstance(ns_dict, dict):
                        log.w("Skipping invalid section", ns, "expected mapping")
                        continue
                    with self.namespace(ns):
                        self._cfg[ns].maps.insert(self._get_user_config_idx(), ns_dict)
            else:
                log.w("Configuration file does not exist", f)
        self._loaded = True
        return self

    def save(self):

        for f in self._files_map:
            log.i("Saving config", f)

            with open(f, 'w', encoding='utf-8') as wf:
                self._ordered_dump(self._files_map[f], wf)

    def save_default(self):
        with open(constants.config_example_path, 'w', encoding='utf-8') as wf:
                self._ordered_dump(self._default_config, wf)

    def apply_commandline_args(self, config_dict):
        for ns in self._cfg:
            cmd_cfg = config_dict.get(ns.lower(), {})
            if not isinstance(cmd_cfg, dict):
                raise ValueError("Expected a dict")
            idx = 1 if self._tmp_context else 0
            self._cfg[ns].maps.insert(idx, cmd_cfg)
        self._cmd_args_applied = True

    def __contains__(self, key):
        assert self._current_ns, "No namespace has been set"
        return key.lower() in self._cfg[self._current_ns]

    def _get_user_config_idx(self):
        idx = 0
        if self._cmd_args_applied:
            idx += 1
        if self._tmp_context:
            idx += 1
        return idx

    def _get_namespace(self, ns):
        return ns.lower().capitalize()

    def key_exists(self, ns, key):
        ""
        ns = self._get_namespace(ns)
        key = key.lower()
        if ns in self._cfg and key in self._cfg[ns]:
            return True
        return False

    def update(self, key, value, user=True):
        "Update a setting. Returns value"
        assert self._current_ns, "No namespace has been set"
        if key not in self._cfg[self._current_ns]:
            raise exceptions.CoreError(
                "Config.update",
                "key '{}' doesn't exist in namespace '{}'".format(
                    key,
                    self._current_ns))
        
        cfg = self._cfg[self._current_ns].maps[self._get_user_config_idx() if user else 0]
        cfg[key] = value
        return value

    @contextmanager
    def namespace(self, ns):
        assert isinstance(ns, str), "Namespace must be str"
        ns = self._get_namespace(ns)
        self._cfg.setdefault(ns, ChainMap())
        self._current_ns = ns
        yield
        self._current_ns = None

    def get(self, ns, key, default=None, description="", create=True, type_=None):
        ""
        if not self._loaded:
            self.load()
        key = key.lower()
        with self.namespace(ns):
            if key not in self._cfg[self._current_ns] and create:
                self.define(key, default, description)

            try:
                v = self._cfg[self._current_ns][key]
            except KeyError:
                if default is None:
                    raise
                return default

            if type_ and not isinstance(v, type_):
                return default
            return v

    def define(self, key, value, description=""):
        assert self._current_ns, "No namespace has been set"
        key = key.lower()
        if description:
            self._comments.setdefault(self._current_ns, {})[key] = description
        self._default_config.setdefault(self._current_ns, OrderedDict())[key] = value
        if self._default_config[self._current_ns] not in self._cfg[self._current_ns].maps:
            self._cfg[self._current_ns].maps.append(self._default_config[self._current_ns])

    def doc_render(self):
        """
        # [
        #   [
        #    [[val1, val2, val3], ...]],
        #    "header descr"
        #   ],
        # ]
        """
        sections = []
        for s in self._default_config:
            con = []
            for key in self._default_config[s]:
                con.append([key, self._default_config[s][key], self._comments[s][key]])
            sections.append([con, s])
        return sections

config = Config(constants.config_path)

core_ns = 'core'

debug = config.create(core_ns, 'debug', False, "Run in debug mode")

concurrent_image_tasks = config.create(
    core_ns,
    "concurrent_image_tasks",
    10,
    "Amount of image service tasks allowed to run at the same time")

secret_key = config.create(
    core_ns,
    "secret_key",
    "",
    "A secret key to be used for security. Keep it secret!")

server_name = config.create(
    core_ns,
    'server_name',
    "happypanda_" +
    base64.urlsafe_b64encode(
        os.urandom(5)).rstrip(b'=').decode('ascii'),
    "Specifiy name of the server")

port = config.create(
    core_ns,
    'port',
    7007,
    "Specify which port to start the server on")

port_web = config.create(
    core_ns,
    'port_web',
    7008,
    "Specify which port to start the webserver on")

port_torrent = config.create(
    core_ns,
    'torrent_port',
    7006,
    "Specify which port to start the torrent client on")

port_range = config.create(core_ns,
    'port_range',
    {'from':7009, 'to':7018},
    "Specify a range of ports to attempt")

host = config.create(
    core_ns,
    'host',
    'localhost',
    "Specify which address the server should bind to")

host_web = config.create(
    core_ns,
    'host_web',
    '',
    "Specify which address the webserver should bind to")

expose_server = config.create(
    core_ns,
    'expose_server',
    False,
    "Attempt to expose the server through portforwading")

allowed_clients = config.create(
    core_ns,
    'allowed_clients',
    0,
    "Limit amount of clients allowed to be connected (0 means no limit)")

allow_guests = config.create(
    core_ns,
    "allow_guests",
    True,
    "Specify if guests are allowed on this server")

require_auth = config.create(
    core_ns,
    "require_auth",
    False,
    "Client must be authenticated to get write access")

disable_default_user = config.create(
    core_ns,
    "disable_default_user",
    False,
    "Disable default user")

session_span = config.create(
    core_ns,
    "session_span",
    60,
    "Specify the amount of time (in minutes) a session can go unused before expiring")

search_ns = 'search'

search_option_regex = config.create(
    search_ns,
    "regex",
    False,
    "Allow regex in search filters")
search_option_case = config.create(
    search_ns,
    "case_sensitive",
    False,
    "Search filter is case sensitive")
search_option_whole = config.create(
    search_ns,
    "match_whole_words",
    False,
    "Match terms exact")
search_option_all = config.create(
    search_ns,
    "match_all_terms",
    True,
    "Match only items that has all terms")

search_option_desc = config.create(
    search_ns,
    "descendants",
    True,
    "Also match on descandants")

client_ns = "client"

translation_locale = config.create(
    client_ns,
    "translation_locale",
    "en_us",
    "The default translation locale when none is specified. See folder /translations for available locales")

config_doc = config.doc_render()  # for doc