from sys import exit
from os import chdir, path

# Change current working directory. This makes it so run.py is required to be on the same level as the happypanda folder
chdir(path.abspath(path.dirname(__file__)))

if __name__ == '__main__':
    from happypanda.core import interface

    interface.interactive()

