import os
import rarfile
import enum

debug = False
dev = False

## VERSIONING ##
version = (0, 0, 1)
version_db = (0,)

## PATHS & FILENAMES ##
dir_root = ''
dir_data = os.path.join(dir_root, "data")
dir_download = os.path.join(dir_root, "downloads")
dir_settings = os.path.join(dir_root, "settings")
dir_cache = os.path.join(dir_root, "cache")
dir_log = os.path.join(dir_root, "logs")
dir_temp = 'temp' # TODO: create temp folder, use python temp facilities
dir_plugin = 'plugins'
log_error = os.path.join(dir_log, "error.log")
log_normal = os.path.join(dir_log, "activity.log")
log_debug = os.path.join(dir_log, "debug.log")
db_name = "happypanda.db"
db_name_dev = "happypanda_dev.db"
db_path = os.path.join(dir_root, dir_data, db_name)
db_path_dev = os.path.join(dir_root, dir_data, db_name_dev)

supported_images = ('.jpg', '.bmp', '.png', '.gif', '.jpeg')
supported_archives = ('.zip', '.cbz', '.rar', '.cbr')

rarfile.PATH_SEP = '/'

## CORE
class ExitCode(enum.Enum):
    Exit = 0
    Restart = 1

core_plugin = None

## DATABASE
db_session = None
default_user = None

## SERVER
server_name = 'server'

port = 7007
port_webserver = port + 1
port_torrent = port_webserver + 1
port_range = range(7007, 7018)

host = "localhost"
host_web = ""
expose_server = False
expose_webserver = False
exposed_server = False
exposed_webserver = False

client_limit = None
postfix = b'<END>'
data_size = 1024
public_server = False
server_ready = True

## NETWORK
