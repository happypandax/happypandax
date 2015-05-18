import os
from ..utils import IMG_FILES as IMF

IMG_FILES = IMF

THUMBNAIL_PATH = os.path.join("db", "thumbnails")
DB_PATH = os.path.join("db","sadpanda.db")
DB_VERSION = [0.12] # a list of accepted db versions. E.g. v3.5 will be backward compatible with v3.1 etc.
CURRENT_DB_VERSION = DB_VERSION[0]
