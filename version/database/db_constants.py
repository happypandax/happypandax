import os

SERIES_PATH = "" #your folder for series here
IMG_FILES = ['jpg','bmp','png','gif']

DB_PATH = os.path.join("db","sadpanda.db")
DB_VERSION = [0.3] # a list of accepted db versions. E.g. v3.5 will be backward compatible with v3.1 etc.
CURRENT_DB_VERSION = DB_VERSION[0]
