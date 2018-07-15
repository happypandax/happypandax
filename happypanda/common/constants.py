import os
import sys
import rarfile
import enum
import itertools
import weakref

rarfile.PATH_SEP = '/'

preview = False
dev = False
dev_db = False
is_installed = os.path.exists(".installed")  # user installed with installer
is_frozen = getattr(sys, 'frozen', False)

is_osx = sys.platform.startswith('darwin')
is_win = os.name == 'nt'
is_linux = sys.platform.startswith("linux") or sys.platform.startswith("linux2")
is_posix = os.name == 'posix'

from_gui = False  # running from gui

executable_name = "happypandax"
if is_win:
    executable_name += ".exe"
executable_gui_name = "happypandax_gui"
if is_win:
    executable_gui_name += ".exe"

# OSX
osx_bundle_name = "HappyPanda X.app"  # used by boostratp deploy, updater and specfile

## UPDATER ##
updater_name = "happyupd"  # windows will make it require escalted priv. if named anything 'updater'
updater_key = "updater"

## VERSIONING ##
build = 134
version = (0, 2, 0)
version_db = (0, 1, 1)
version_web = (0, 2, 0)
version_str = ".".join(str(x) for x in version)
version_db_str = ".".join(str(x) for x in version_db)
version_web_str = ".".join(str(x) for x in version_web)

## PATHS & FILENAMES ##
app_path = getattr(sys, '_MEIPASS', '.') if is_frozen else '.'
dir_root = ""
dir_static = os.path.join(dir_root, "static")
dir_bin = os.path.join(dir_root, "bin", "win32" if is_win else "osx" if is_osx else "linux" if is_linux else "")
dir_data = os.path.join(dir_root, "data")
dir_download = os.path.join(dir_root, "downloads")
dir_cache = os.path.join(dir_data, "cache")
dir_certs = os.path.join(dir_data, "certs")
dir_update = os.path.join(dir_cache, "happyupdate")
dir_log = os.path.join(dir_root, "logs")
dir_temp = os.path.join(dir_cache, "temp")
dir_plugin = os.path.join(dir_root, "plugins")
dir_templates = os.path.join(dir_root, "templates")
dir_thumbs = os.path.join(dir_static, "thumbnails")
dir_translations = os.path.join(dir_root, "translations")
config_path = os.path.join(dir_root, "config.yaml")
config_example_path = os.path.join(dir_root, "config-example.yaml")
log_error = os.path.join(dir_log, "error.log")
log_normal = os.path.join(dir_log, "activity.log")
log_debug = os.path.join(dir_log, "debug.log")
log_plugin = os.path.join(dir_log, "plugin.log")
db_name = "happypanda"
db_name_dev = "happypanda_dev"
db_path = os.path.join(dir_root, dir_data, db_name + '.db')
db_path_dev = os.path.join(dir_root, dir_data, db_name_dev + '.db')
internal_db_path = os.path.join(dir_data, "internals.db")
favicon_path = os.path.join(dir_static, "favicon", "favicon.ico")

migration_config_path = os.path.join(dir_root, "alembic.ini")

thumbs_view = "/thumb"
link_ext = '.link'

# CORE
store = None
invalidator = None
internaldb = None
web_proc = None  # webserver process
notification = None  # ClientNotifications

general_counter = itertools.count(50)
default_temp_view_id = 1

notif_normal_timeout = 45
notif_small_timeout = 15
notif_long_timeout = 80

log_format = '%(asctime)-6s--%(levelname)-6s %(name)-10s: %(message)s'
log_datefmt = '%b-%m %H:%M:%S'
log_plugin_format = log_format
log_plugin_datefmt = log_datefmt
log_size = 100000 * 10  # 10mb
log_ns_plugincontext = 'pluginctx.'
log_ns_core = '[core].'
log_ns_command = '[command].'
log_ns_plugin = '[plugin].'
log_ns_database = '[database].'
log_ns_server = '[server].'
log_ns_client = '[client].'
log_ns_gui = '[gui].'
log_ns_network = '[network].'
log_ns_search = '[search].'
log_ns_misc = '[misc].'
log_namespaces = (x[:-1] for x in (
    log_ns_core,
    log_ns_command,
    log_ns_plugin,
    log_ns_database,
    log_ns_server,
    log_ns_client,
    log_ns_gui,
    log_ns_network,
    log_ns_search,
    log_ns_misc,
    log_ns_plugincontext
))

task_command = None  # TaskService.TaskList of TaskService commands


class Dialect:
    SQLITE = "sqlite"
    MYSQL = "mysql"
    POSTGRES = "postgres"


class ExitCode(enum.Enum):
    Exit = 0
    Restart = 10
    Update = 20


class UpdateState(enum.Enum):
    Registered = 0
    Installing = 1
    Failed = 2
    Success = 3


class Priority(enum.Enum):
    High = 10
    Normal = 5
    Low = 0


class PushID(enum.Enum):
    Update = 1
    User = 200


super_user_name = "default"

maximum_native_workers = 15

command_progress_removal_time = 60 * 5  # seconds

is_new_db = False

image_sizes = {
    "big": (300, 416),
    "medium": (200, 276),
    "small": (100, 136),
}

translations = None  # dict of available translation files

services = weakref.WeakValueDictionary()  # servicetype.service_name (all lowercase)

# PLUGIN

plugin_interface_name = "__hpx__"
plugin_manager = None
available_commands = {'event': set(), 'entry': set(), 'class': {}}
plugin_shortname_length = 20

# DATABASE
db_engine = None
db_session = None
_db_scoped_session = None
default_user = None
special_namespace = "__namespace__"

scheduler_database_url = os.path.join("sqlite:///", dir_data, "scheduler.db")

# SERVER

exposed_server = False

postfix = b'<EOF>'
data_size = 4096
server_ready = True
server_started = False
local_ip = ""
public_ip = ""
