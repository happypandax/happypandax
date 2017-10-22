import os
import rarfile
import enum

rarfile.PATH_SEP = '/'

dev = False

## VERSIONING ##
build = 104
version = (0, 0, 1)
version_db = (0, 0, 1)

## PATHS & FILENAMES ##
dir_root = ''
dir_static = os.path.join(dir_root, "static")
dir_data = os.path.join(dir_root, "data")
dir_download = os.path.join(dir_root, "downloads")
dir_cache = os.path.join(dir_data, "cache")
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

thumbs_view = "/thumb"
link_ext = '.link'

# CORE


class ExitCode(enum.Enum):
    Exit = 0
    Restart = 1


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

# CLIENT

# PLUGIN

core_plugin = None
plugin_manager = None
available_commands = set()
available_events = set()
plugin_shortname_length = 10

# DATABASE½
db_engine = None
db_session = None
_db_scoped_session = None
default_user = None
special_namespace = "__namespace__"

# SERVER

exposed_server = False

postfix = b'<EOF>'
data_size = 1024
server_ready = True
local_ip = ""
public_ip = ""
