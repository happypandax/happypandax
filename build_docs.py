import os
from shutil import move
from subprocess import run

run(["sphinx-build", "-b html", "docs/source", "docs/build"])

if os.path.exists("docs/build"):
    b_dir = list(os.scandir("docs/build"))
    for x in b_dir:
        move(os.path.join("docs", "build", x.name), os.path.join("docs", x.name))

    os.rmdir("docs/build")