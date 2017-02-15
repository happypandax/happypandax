__all__ = ["constants", "exceptions", "utils"]

import os
from . import constants

# create paths if they don't exist
for d in (constants.dir_log, constants.dir_data, constants.dir_cache):
    if d:
        if not os.path.isdir(d):
            os.mkdir(d)
