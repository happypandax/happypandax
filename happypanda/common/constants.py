import os
import rarfile
import enum

debug = True # TODO: arg switch

## VERSIONING ##
version = "0.0.1"
version_db = (0,)

## PATHS & FILENAMES ##
dir_root = ''
dir_data = os.path.join(dir_root, "data")
dir_cache = os.path.join(dir_root, "cache")
dir_log = os.path.join(dir_root, "logs")
dir_temp = 'temp' # TODO: create temp folder, use python temp facilities
log_error = os.path.join(dir_log, "error.log")
log_normal = os.path.join(dir_log, "activity.log")
log_debug = os.path.join(dir_log, "debug.log")
db_name = "happypanda.db"
db_name_debug = "happypanda_debug.db"
db_path = os.path.join(dir_root, dir_data, db_name)
db_path_debug = os.path.join(dir_root, dir_data, db_name_debug)

supported_images = ('.jpg', '.bmp', '.png', '.gif', '.jpeg')
supported_archives = ('.zip', '.cbz', '.rar', '.cbr')

rarfile.PATH_SEP = '/'

## CORE
class GalleryFilter(enum.Enum):
    #: Library
    Library = 0
    #: Favourite
    Favorite = 1
    #: Inbox
    Inbox = 2

## DATABASE
db_session = None

class HistoryAction(enum.Enum):
    read = 'read'
    start = 'start'

## SERVER
server_name = 'server'
local_port = 5577
web_port = local_port + 1
localhost = False # localhost only
host = "localhost" if localhost else ""
client_limit = None
postfix = b'end'
data_size = 1024
public_server = False
server_ready = True

