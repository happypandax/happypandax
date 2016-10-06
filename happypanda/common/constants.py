import os

version = "0.0.1"

## PATHS & FILENAMES ##

log_dir = "logs"
error_log = os.path.join(log_dir, "error.log")
normal_log = os.path.join(log_dir, "activity.log")
debug_log = os.path.join(log_dir, "debug.log")