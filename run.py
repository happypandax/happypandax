from os import chdir, path

# Change current working directory. This makes it so run.py is required to be on the same level as the happypanda folder
chdir(path.abspath(path.dirname(__file__)))

# TODO: accept arg to decide which modules to start

if __name__ == '__main__':
    from happypanda.server.core import interface, server

    server.HPServer().run(web=True, interactive=False)
