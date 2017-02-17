import os
import rarfile
import enum
from socket import gethostname

debug = True # TODO: arg switch

## VERSIONING ##
version = "0.0.1"
version_api = "0"
version_db = (0,)

## PATHS & FILENAMES ##
dir_data = "data"
dir_cache = "cache"
dir_log = "logs"
log_error = os.path.join(dir_log, "error.log")
log_normal = os.path.join(dir_log, "activity.log")
log_debug = os.path.join(dir_log, "debug.log")
log_debug = os.path.join(dir_log, "debug.log")
db_name = "happypanda.db"
db_path = os.path.join(dir_data, db_name)

supported_images = ('.jpg', '.bmp', '.png', '.gif', '.jpeg')
supported_archives = ('.zip', '.cbz', '.rar', '.cbr')

rarfile.PATH_SEP = '/'

## DATABASE
db_session = None

## SERVER
local_port = 5577
web_port = local_port + 1
localhost = False
host = "localhost" if localhost else gethostname()
client_limit = None
postfix = b'end'
data_size = 1024
public_server = False

