import os
import yaml
import gevent
import random
import rarfile

from enum import Enum
from contextlib import contextmanager
from collections import ChainMap, OrderedDict

from happypanda.common import exceptions, hlogger, constants

log = hlogger.Logger(constants.log_ns_core + __name__, process="MainProcess")


class ConfigIsolation(Enum):
    server = "server"
    client = "client"


class ConfigNode:

    default_namespaces = set()

    _cfg_nodes = {}

    def __init__(self, cfg, ns, name, value, description="", type_=None,
                 isolation=ConfigIsolation.server, hidden=False, only=None):
        self._cfg = cfg
        self.isolation = isolation
        self.namespace = ns
        self.name = name
        self.fullname = self.namespace + '.' + self.name
        self.default = value
        self.description = description
        self.type_ = type(value) if type_ is None else type_
        self.hidden = hidden
        self._created = False
        self.only = only
        if not hidden:
            with self._cfg.namespace(ns):
                self._cfg.define(name, value, description)
        self.default_namespaces.add(ns.lower())
        self._cfg_nodes.setdefault(ns.lower(), {})[name.lower()] = self
        self._triggers = []

    def add_trigger(self, handler):
        assert callable(handler)
        self._triggers.append(handler)

    @classmethod
    def get_isolation_level(cls, ns, key):
        return cls._cfg_nodes[ns.lower()][key.lower()].isolation

    @classmethod
    def get_type(cls, ns, key):
        return cls._cfg_nodes[ns.lower()][key.lower()].type_

    def _get_ctx_config(self):
        return getattr(gevent.getcurrent(), 'locals', {}).get("ctx", {}).get("config", {})

    def get(self, *args, **kwargs):
        if self.hidden:
            try:
                v = self._cfg.get(*args, **kwargs)
            except KeyError:
                v = self.default
        else:
            v = self._cfg.get(*args, **kwargs)
        return v

    @classmethod
    def get_all(cls):
        return cls._cfg_nodes

    @property
    def value(self):
        with self._cfg.tmp_config(self.namespace, self._get_ctx_config()):
            return self.get(self.namespace, self.name, default=self.default,
                            create=False, type_=self.type_, only=self.only)

    @value.setter
    def value(self, new_value):
        if self.only is not None and new_value not in self.only:
            log.w("Ignoring config value assignment {}:{} to {}".format(self.namespace, self.name, new_value))
            return

        if self.isolation == ConfigIsolation.client:
            with self._cfg.tmp_config(self.namespace, self._get_ctx_config()):
                self._cfg.update(self.name, new_value, create=self.hidden)
        else:
            with self._cfg.namespace(self.namespace):
                self._cfg.update(self.name, new_value, create=self.hidden)

        for h in self._triggers:
            h(self, new_value)

    def __bool__(self):
        return bool(self.value)


class Config:

    def __init__(self, *filepaths, user_filepath=""):
        self._cfg = OrderedDict()
        self._current_ns = None
        self._prev_ns = None
        self._files = filepaths
        self._user_file = user_filepath
        self._files_map = {}
        self._comments = {}
        self._default_config = OrderedDict()
        self._loaded = False
        self._cmd_args_applied = False

    def create(self, ns, key, default=None, description="", type_=None, **kwargs):
        if ns is None:
            ns = self._current_ns
        return ConfigNode(self, ns, key, default, description, type_, **kwargs)

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
        return yaml.dump(data,
                         stream,
                         OrderedDumper,
                         default_flow_style=False,
                         indent=4,
                         **kwds)

    def load(self):
        paths = list(self._files)
        paths.append(self._user_file)
        for f in paths:
            file_dict = OrderedDict()
            if os.path.exists(f):
                log.i("Loading existing configuration from", os.path.abspath(f))
                try:
                    with open(f, 'r', encoding='utf-8') as rf:
                        f_dict = self._ordered_load(rf)
                except yaml.YAMLError:
                    log.exception("Error in configuration file", f)
                    continue

                if not f_dict:
                    log.w("Empty configuration file")
                    f_dict = OrderedDict()
                elif not isinstance(f_dict, dict):
                    log.w("Invalid configuration file, expected mapping")
                    f_dict = OrderedDict()
                for ns in f_dict:
                    ns_dict = f_dict[ns]
                    ns = self.format_namespace(ns)
                    if not isinstance(ns_dict, dict):
                        log.w("Skipping invalid section", ns, "expected mapping")
                        continue
                    with self.namespace(ns):
                        self._cfg[ns].maps.insert(self._get_user_config_idx(), ns_dict)
                file_dict = f_dict
            self._files_map[f] = file_dict
        self._loaded = True
        return self

    def save(self):
        if self._user_file:
            log.i("Saving config", self._user_file)

            f_dict = self._files_map.get(self._user_file)
            if f_dict is not None:
                with open(self._user_file, 'w', encoding='utf-8') as wf:
                    self._ordered_dump(f_dict, wf)
            return True
        return False

    def save_default(self):
        with open(constants.config_example_path, 'w', encoding='utf-8') as wf:
            self._ordered_dump(self._default_config, wf)

    def apply_commandline_args(self, config_dict):
        if not self._cmd_args_applied:
            for ns in self._cfg:
                cmd_cfg = config_dict.get(ns.lower(), {})
                if not isinstance(cmd_cfg, dict):
                    raise ValueError("Expected a dict")
                self._cfg[ns].maps.insert(0, cmd_cfg)
            self._cmd_args_applied = True

    def __contains__(self, key):
        assert self._current_ns, "No namespace has been set"
        return key.lower() in self._cfg[self._current_ns]

    def _get_user_config_idx(self):
        idx = 0
        if self._cmd_args_applied:
            idx += 1
        return idx

    def format_namespace(self, ns):
        return ns.lower()

    def key_exists(self, ns, key):
        ""
        ns = self.format_namespace(ns)
        key = key.lower()
        if ns in self._cfg and key in self._cfg[ns]:
            return True
        return False

    def update(self, key, value, user=True, create=False):
        "Update a setting. Returns value"
        assert self._current_ns, "No namespace has been set"
        if not create:
            if key not in self._cfg[self._current_ns]:
                raise exceptions.CoreError(
                    "Config.update",
                    "key '{}' doesn't exist in namespace '{}'".format(
                        key,
                        self._current_ns))
        if user:
            user_cfg = self._files_map.get(self._user_file)
            if user_cfg is not None:
                u_cfg = user_cfg.setdefault(self._current_ns, {})
                u_cfg[key] = value
                if u_cfg not in self._cfg[self._current_ns].maps:
                    self._cfg[self._current_ns].maps.insert(self._get_user_config_idx(), u_cfg)
        else:
            self._cfg[self._current_ns][key] = value
        return value

    @contextmanager
    def tmp_config(self, ns, cfg):
        if not cfg:
            yield
            return
        if ns is not None:
            ns = self.format_namespace(ns)
            with self.namespace(ns):
                tmp = self._current_ns not in self._cfg
                tmp_cfg = cfg.setdefault(ns, {})
                self._cfg[self._current_ns] = self._cfg[self._current_ns].new_child(tmp_cfg)
                yield
                self._cfg[self._current_ns] = self._cfg[self._current_ns].parents
                if tmp:
                    self._cfg.pop(self._current_ns)
        else:
            tmp_ns = []
            for ns, tmp_cfg in cfg.items():
                curr_ns = self.format_namespace(ns)
                if curr_ns not in self._cfg:
                    tmp_ns.append(curr_ns)
                with self.namespace(curr_ns):
                    self._cfg[self._current_ns] = self._cfg[self._current_ns].new_child(tmp_cfg)
            yield
            for ns in cfg:
                with self.namespace(ns):
                    self._cfg[self._current_ns] = self._cfg[self._current_ns].parents
            for n in tmp_ns:
                self._cfg.pop(n)

    @contextmanager
    def namespace(self, ns):
        assert isinstance(ns, str), "Namespace must be str"
        ns = self.format_namespace(ns)
        self._cfg.setdefault(ns, ChainMap())
        self._prev_ns = self._current_ns
        self._current_ns = ns
        yield
        self._current_ns = self._prev_ns

    def get(self, ns, key, default=None, description="", create=False, type_=None, only=None):
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

            if v is None:
                return default

            if type_ is not None and not isinstance(v, type_):
                log.w(
                    "Setting '{}.{}' expected '{}' but got '{}', using default value".format(
                        ns, key, type_, type(v)), stderr=True)
                return default

            if only is not None and v not in only:
                log.w(
                    "Setting '{}:{}' expected one of {}, using default value '{}'".format(
                        ns, key, only, default), stderr=True)
                return default
            return v

    def get_all(self):
        "Returns a dict with all available settings with their current value"
        s = {}
        for ns in self._cfg:
            s[ns.lower()] = {}
            for m in reversed(self._cfg[ns].maps):
                s[ns.lower()].update(m)
        return s

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
        for s in sorted(ConfigNode._cfg_nodes):
            con = []
            for key, node in sorted(ConfigNode._cfg_nodes[s].items(), key=lambda a: a[0]):
                if node.hidden:
                    continue
                con.append([key, node.default or '', node.isolation.value, node.description])
            sections.append([con, s])
        return sections


def get_best_girls():
    best_girls = (
        'ram',
        'rias',
        'hinata',
        'sena',
        'orihime',
        'saeko',
        'emilia',
        'yumiko',
        'momo',
        'shinobu',
        'mayoi',
        'testarossa',
        'yami',
        'mikan',
        'eri',
        'yakumo',
        'kouko',
        'krista',
        'naoka',
        'lacus',
        'albedo',
    )
    return "_".join(best_girls[random.randrange(0, len(best_girls))] for x in range(3))


config = Config(user_filepath=constants.config_path)

core_ns = 'core'

with config.namespace(core_ns):

    debug = config.create(core_ns, 'debug', False, "Run in debug mode")

    secret_key = config.create(
        core_ns,
        "secret_key",
        "",
        "A secret key to be used for security. Keep it secret!", hidden=True)

    report_critical_errors = config.create(
        core_ns,
        'report_critical_errors',
        True,
        "Send occurring critical errors to me (creator) so I can fix them faster")

    concurrent_image_tasks = config.create(
        core_ns,
        "concurrent_image_tasks",
        10,
        "Amount of image service tasks allowed to run at the same time (higher count does not necessarily mean faster generation)")

    concurrent_network_tasks = config.create(
        core_ns,
        "concurrent_network_tasks",
        50,
        "Amount of network service tasks allowed to run at the same time (higher count does not necessarily mean faster network speed)")

    check_new_releases = config.create(
        core_ns,
        "check_new_releases",
        True,
        "Regularly check for updates")

    auto_install_release = config.create(
        core_ns,
        "auto_install_release",
        True,
        "Automatically download, install and restart when a new update is found")

    check_release_interval = config.create(
        core_ns,
        "check_release_interval",
        20,
        "Interval in minutes between checking for a new update, set 0 to only check once every startup")

    allow_beta_releases = config.create(
        core_ns,
        "allow_beta_releases",
        True,
        "Allow downloading beta releases")

    allow_alpha_releases = config.create(
        core_ns,
        "allow_alpha_releases",
        False,
        "Allow downloading alpha releases")

    unrar_tool_path = config.create(
        core_ns,
        "unrar_tool_path",
        os.path.join(constants.dir_bin, "unrar.exe") if constants.is_win else "unrar",
        "Path to unrar tool. On Windows the default path is 'bin/win32/unrar.exe'. On Unix the default path is 'unrar'")

    auto_thumb_clean_size = config.create(
        core_ns,
        "auto_thumb_clean_size",
        400,
        "Maximum size in megabytes to which the thumbnail folder will automatically get emptied when exceeded")

    auto_temp_clean_size = config.create(
        core_ns,
        "auto_temp_clean_size",
        500,
        "Maximum size in megabytes to which the temp folder will automatically get emptied when exceeded")


plugin_ns = 'plugin'

with config.namespace(plugin_ns):
    auto_install_plugin = config.create(
        None,
        "auto_install_plugin",
        False,
        "Automatically install a discovered plugin")

    auto_install_plugin_dependency = config.create(
        None,
        "auto_install_plugin_dependency",
        True,
        "Automatically install a plugin's dependencies when installing a plugin")

    plugin_dir = config.create(
        None,
        "plugin_dir",
        "",
        "Additional optional plugin directory to look for plugins")

gallery_ns = 'gallery'

with config.namespace(gallery_ns):

    external_image_viewer = config.create(
        gallery_ns,
        "external_image_viewer",
        "",
        "Path to external image viewer executable")

    external_image_viewer_args = config.create(
        gallery_ns,
        "external_image_viewer_args",
        "",
        "Command arguments to supply the image viewer executable")

    send_to_trash = config.create(
        gallery_ns,
        "send_to_trash",
        True,
        "Send deleted galleries to recycle bin")

    send_path_to_first_file = config.create(
        gallery_ns,
        "send_path_to_first_file",
        False,
        "Send path to first file when opening a gallery in external viewer",
    )

    add_to_inbox = config.create(
        gallery_ns,
        "add_to_inbox",
        True,
        "Add new galleries to inbox",
        isolation=ConfigIsolation.client
    )

    auto_rate_gallery_on_favorite = config.create(
        gallery_ns,
        "auto_rate_on_favorite",
        True,
        "Automatically set unrated galley rating to highest on favorite")


db_ns = 'db'

with config.namespace(db_ns):

    dialect = config.create(
        db_ns,
        "dialect",
        "sqlite",
        "Which SQL dialect to use between 'sqlite' and 'postgres'. " +
        "Note that HPX will not transfer data from one dialect to another once chosen. " +
        "It is therefore advised that you choose a dialect early and stick to it throughout. " +
        "Only Postgres version 9.4 and up is supported",
        only=("sqlite", "postgres"))

    db_name = config.create(
        db_ns,
        "name",
        constants.db_name,
        "Database name. This setting does not apply when the SQLite dialect is used")

    db_username = config.create(
        db_ns,
        "username",
        None,
        "Database user name. This setting does not apply when the SQLite dialect is used",
        type_=str)

    db_password = config.create(
        db_ns,
        "password",
        None,
        "Database password. This setting does not apply when the SQLite dialect is used",
        type_=str)

    db_host = config.create(
        db_ns,
        "host",
        None,
        "Database host. This setting does not apply when the SQLite dialect is used",
        type_=str)

    db_port = config.create(
        db_ns,
        "port",
        None,
        "Database port. This setting does not apply when the SQLite dialect is used",
        type_=int)

    db_query = config.create(
        db_ns,
        "query",
        {},
        "A mapping of options to be passed to the database upon connect",
        type_=dict)

    sqlite_database_timeout = config.create(
        db_ns,
        "sqlite_database_timeout",
        30,
        "Amount of seconds to wait for the database to be writeable")

    pool_size = config.create(
        db_ns,
        "pool_size",
        15,
        "The size of the pool to be maintained. This is the largest number of connections that will be kept persistently in the pool. " +
        "This setting does not apply when the SQLite dialect is used")

    pool_timeout = config.create(
        db_ns,
        "pool_timeout",
        45,
        "The number of seconds to wait before giving up on returning a connection. " +
        "This setting does not apply when the SQLite dialect is used")

server_ns = 'server'

with config.namespace(server_ns):

    server_name = config.create(
        server_ns,
        'server_name',
        get_best_girls(),
        "Specifiy name of the server")

    port = config.create(
        server_ns,
        'port',
        7007,
        "Specify which port to start the server on")

    port_web = config.create(
        server_ns,
        'port_web',
        7008,
        "Specify which port to start the webserver on")

    port_torrent = config.create(
        server_ns,
        'torrent_port',
        7006,
        "Specify which port to start the torrent client on")

    port_range = config.create(server_ns,
                               'port_range',
                               {'from': 7009, 'to': 7018},
                               "Specify a range of ports to attempt")

    host = config.create(
        server_ns,
        'host',
        'localhost',
        "Specify which address the server should bind to")

    host_web = config.create(
        server_ns,
        'host_web',
        '',
        "Specify which address the webserver should bind to")

    expose_server = config.create(
        server_ns,
        'expose_server',
        False,
        "Attempt to expose the server through portforwading")

    allowed_clients = config.create(
        server_ns,
        'allowed_clients',
        0,
        "Limit amount of clients allowed to be connected (0 means no limit)")

    allow_guests = config.create(
        server_ns,
        "allow_guests",
        True,
        "Specify if guests are allowed on this server")

    require_auth = config.create(
        server_ns,
        "require_auth",
        False,
        "Client must be authenticated to get write access")

    disable_default_user = config.create(
        server_ns,
        "disable_default_user",
        False,
        "Disable default user")

    session_span = config.create(
        server_ns,
        "session_span",
        0,
        "Specify the amount of time (in minutes) a session can go unused before expiring or 0 for never")

    enable_ssl = config.create(server_ns, "enable_ssl", False,
                               'Enable SSL, valid values are true/false or "server"/"web" to only enable for the specific component',
                               type_=(str, bool))

    server_cert = config.create(server_ns,
                                "server_cert",
                                {'certfile': None,
                                 'keyfile': None},
                                "Path to a certificate and the corresponding private key. If keyfile is not set, the private key will be taken from certfile. " +
                                "Note that if SSL is enabled and no cert files are provided, a self-signed certificate will be created and used instead. " +
                                "The self-signed certificate can be found at data/certs/")

    web_cert = config.create(server_ns,
                             "web_cert",
                             {'certfile': None,
                                 'keyfile': None},
                             "Same as server_cert. Values are inherited from server_cert If no values are provided and SSL is enabled for 'web' too")


search_ns = 'search'

with config.namespace(search_ns):

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

scan_ns = "scan"

with config.namespace(scan_ns):

    skip_existing_galleries = config.create(
        None,
        "skip_existing_galleries",
        True,
        "Skip galleries that have already been added to HPX",
        isolation=ConfigIsolation.client)

client_ns = "client"

with config.namespace(client_ns):

    translation_locale = config.create(
        client_ns,
        "translation_locale",
        "en_us",
        "The default translation locale when none is specified. See folder /translations for available locales",
        isolation=ConfigIsolation.client
    )

gui_ns = "gui"

with config.namespace(gui_ns):

    gui_start_on_boot = config.create(
        None,
        "start_on_boot",
        False,
        "Start HPX GUI automatically on boot")

    gui_autostart_server = config.create(
        None,
        "autostart_server",
        False,
        "Start the server automatically on HPX GUI startup")

    gui_start_minimized = config.create(
        None,
        "start_minimized_to_tray",
        False,
        "Start the HPX GUI in a minimized to tray state")

    gui_minimize_on_close = config.create(
        None,
        "send_to_tray_on_close",
        False,
        "Put the application in the notification tray on close button")

    gui_minimize_on_minimize = config.create(
        None,
        "send_to_tray_on_minimize",
        False,
        "Put the application in the notification tray on minimize button")

    gui_open_webclient_on_server_start = config.create(
        None,
        "open_webclient_on_server_start",
        True,
        "Open the webclient in your default browser on server start")

network_ns = "network"

with config.namespace(network_ns):

    request_timeout = config.create(
        None,
        "request_timeout",
        30,
        "Upper limit of a request timeout in seconds")

    proxy = config.create(
        None,
        "proxy",
        {'http': '', 'https': ''},
        "Specify network proxies. Proxy URLs must include the scheme. To use HTTP Basic Auth with your proxy, use the http://user:password@host/ syntax")

advanced_ns = "advanced"

with config.namespace(advanced_ns):

    dev_db = config.create(
        advanced_ns,
        "dev_db",
        False,
        "Use a dev database", hidden=True)

    rollbar_access_token = config.create(
        advanced_ns,
        "rollbar_access_token",
        "3c1a82d8dd054c098d2c49f30615624a",
        "Rollbar access token", hidden=True)

    github_repo = config.create(
        advanced_ns,
        "github_repo",
        {'repo': 'server', 'owner': 'happypandax'},
        "Github repo and owner", hidden=True)

    checksum_provider_repo = config.create(
        advanced_ns,
        "checksum_provider_repo",
        {'repo': 'updates', 'owner': 'happypandax', 'file': 'checksums.txt'},
        "Github repo and owner and file", hidden=True)

    sevenzip_path = config.create(
        advanced_ns,
        "7z_path",
        "",
        "Path to the 7z executable", hidden=True)

    enabled_loggers = config.create(
        advanced_ns,
        "enabled_loggers",
        [],
        "Loggers to enable. Available loggers: {}".format(",".join((
            x[:-1] for x in (
                constants.log_ns_client,
                constants.log_ns_command,
                constants.log_ns_core,
                constants.log_ns_database,
                constants.log_ns_gui,
                constants.log_ns_network,
                constants.log_ns_plugin,
                constants.log_ns_search,
                constants.log_ns_server,
                constants.log_ns_misc
            )))))

config_doc = config.doc_render()  # for doc

rarfile.UNRAR_TOOL = unrar_tool_path.value


def set_unrartool(node, value):
    rarfile.UNRAR_TOOL = value


unrar_tool_path.add_trigger(set_unrartool)
