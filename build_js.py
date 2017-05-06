import os

from subprocess import run

js_dir = "happypanda/webclient/static"
# Note: 
# Transcrypt is required to be in the same directory as the js files
os.chdir(js_dir)

run(["transcrypt", "-b", "-m", "-e", "6", "-n", ".\pages.py"])