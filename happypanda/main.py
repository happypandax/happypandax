import os, sys

if __package__ is None and not hasattr(sys, 'frozen'):
    # direct call of main.py
    path = os.path.realpath(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(os.path.dirname(path)))

from happypanda.common import utils, constants
from happypanda.server.core import server, plugins

def start():
    utils.setup_dirs()
    parser = utils.get_argparser()
    args = parser.parse_args()
    utils.parse_options(args)
    utils.setup_logger(args)

    constants.core_plugin = plugins._plugin_load("happypanda.server.core.coreplugin", "core")

    if not args.safe:
        plugins.plugin_loader(constants.dir_plugin)
    else:
        plugins.registered.init_plugins()

    server.HPServer().run(web=args.web, interactive=args.interact)

if __name__ == '__main__':
    start()