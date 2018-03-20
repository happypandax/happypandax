import os
import sys
import rarfile
import enum

rarfile.PATH_SEP = '/'

preview = True
dev = False
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
build = 122
version = (0, 0, 11)
version_db = (0, 0, 2)
version_web = (0, 0, 10)
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
db_name = "happypanda.db"
db_name_dev = "happypanda_dev.db"
db_path = os.path.join(dir_root, dir_data, db_name)
db_path_dev = os.path.join(dir_root, dir_data, db_name_dev)
internal_db_path = os.path.join(dir_data, "internals")

thumbs_view = "/thumb"
link_ext = '.link'

# CORE
invalidator = None
internaldb = None
web_proc = None  # webserver process
notification = None  # ClientNotifications

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


maximum_native_workers = 15

command_progress_removal_time = 60 * 5  # seconds

is_new_db = False

image_sizes = {
    "big": (300, 416),
    "medium": (200, 276),
    "small": (100, 136),
}

translations = None  # dict of available translation files

# PLUGIN

core_plugin = None
plugin_manager = None
available_commands = set()
available_events = set()
plugin_shortname_length = 10

# DATABASE
db_engine = None
db_session = None
_db_scoped_session = None
default_user = None
special_namespace = "__namespace__"

# SERVER

exposed_server = False

postfix = b'<EOF>'
data_size = 4096
server_ready = True
server_started = False
local_ip = ""
public_ip = ""
