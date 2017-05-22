import os
import rarfile
import enum
import base64

from happypanda.common import config as cfg

rarfile.PATH_SEP = '/'

dev = False

## VERSIONING ##
version = (0, 0, 1)
version_db = (0, 0, 1)
version_web = (0, 0, 1)

## PATHS & FILENAMES ##
dir_root = ''
dir_data = os.path.join(dir_root, "data")
dir_download = os.path.join(dir_root, "downloads")
dir_settings = os.path.join(dir_root, "settings")
dir_cache = os.path.join(dir_data, "cache")
dir_log = os.path.join(dir_root, "logs")
dir_temp = 'temp' # TODO: create temp folder, use python temp facilities
dir_plugin = 'plugins'
settings_file = "settings.ini"
settings_descr_file = ".settings"
log_error = os.path.join(dir_log, "error.log")
log_normal = os.path.join(dir_log, "activity.log")
log_debug = os.path.join(dir_log, "debug.log")
db_name = "happypanda.db"
db_name_dev = "happypanda_dev.db"
db_path = os.path.join(dir_root, dir_data, db_name)
db_path_dev = os.path.join(dir_root, dir_data, db_name_dev)

supported_images = ('.jpg', '.bmp', '.png', '.gif', '.jpeg')
supported_archives = ('.zip', '.cbz', '.rar', '.cbr')

core_ns = 'core'
config = cfg.Config(dir_root, settings_file, settings_descr_file)

debug = config.get(core_ns, 'debug', False, "Run in debug mode")

preview = config.get(core_ns, 'preview', False, "Run in preview mode")

## CORE
class ExitCode(enum.Enum):
    Exit = 0
    Restart = 1

class RuntimeMode(enum.Enum):
    Server = 0
    User = 0

running_mode = RuntimeMode.User

core_plugin = None

allowed_tasks = 10

## DATABASE
db_session = None
default_user = None

## SERVER
server_name = config.get(core_ns, 'server_name', "happypanda_"+base64.urlsafe_b64encode(os.urandom(5)).rstrip(b'=').decode('ascii'), "Specifiy name of the server")

port = config.get(core_ns, 'port', 7007, "Specify which port to start the server on")
port_webserver = config.get(core_ns, 'port_webserver', port+1, "Specify which port to start the webserver on")
port_torrent = config.get(core_ns, 'port_torrent', port_webserver+1, "Specify which port to start the torrent client on")
port_range = range(*(int(x) for x in config.get(core_ns, 'port_range', '7007-7018', "Specify a range of ports to attempt").split('-')))

host = config.get(core_ns, 'host', 'localhost', "Specify which address the server should bind to")
host_web = config.get(core_ns, 'host_web', '', "Specify which address the webserver should bind to")
expose_server =  config.get(core_ns, 'expose_server', False, "Attempt to expose the server through portforwading")
expose_webserver = config.get(core_ns, 'expose_webserver', False, "Attempt to expose the webserver through portforwading")
exposed_server = False
exposed_webserver = False

allowed_clients = config.get(core_ns, 'allowed_clients', 0, "Limit amount of clients allowed to be connected (0 means no limit)")
postfix = b'<END>'
data_size = 1024
server_ready = True

## NETWORK

config_doc = config.doc_render() # for doc
