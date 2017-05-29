from sys import exit
from os import chdir, path
from subprocess import run

# Change current working directory. This makes it so run_tests.py is required to be on the same level as the happypanda folder
chdir(path.abspath(path.dirname(__file__)))


if __name__ == '__main__':
    exit(run(["pytest", "tests"]).returncode)