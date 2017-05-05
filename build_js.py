import os

from subprocess import run

# Note: 
# Transcrypt is required to be in the same directory as the js files
os.chdir("happypanda/webclient/static")

run(["transcrypt", "-b", "-m", "-e", "6", "-n", ".\client.py"])