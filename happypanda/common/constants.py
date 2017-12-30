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
is_linux = os.name == 'posix'

from_gui = False  # running from gui

## UPDATER ##
updater_name = "happyupd"  # windows will make it require escalted priv. if named anything 'updater'
updater_key = "updater"

## VERSIONING ##
build = 111
version = (0, 0, 2)
version_db = (0, 0, 1)
version_web = (0, 0, 2)

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

web_proc = None  # webserver process
notification = None  # ClientNotifications


class ExitCode(enum.Enum):
    Exit = 0
    Restart = 10
    Update = 20


class UpdateState(enum.Enum):
    Registered = 0
    Failed = 1
    Success = 2


class Priority(enum.Enum):
    High = 10
    Normal = 5
    Low = 0


maximum_native_workers = 15

image_sizes = {
    "big": (300, 416),
    "medium": (200, 276),
    "small": (100, 136),
}

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
