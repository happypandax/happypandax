import os
import sys

if __package__ is None and not hasattr(sys, 'frozen'):
    # direct call of main.py
    path = os.path.realpath(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(os.path.dirname(path)))

from happypanda.common import utils, constants  # noqa: E402
from happypanda.server.core import server, plugins, command  # noqa: E402
from happypanda.webclient import main as webserver  # noqa: E402

log = utils.Logger(__name__)


def start():
    utils.setup_dirs()
    parser = utils.get_argparser()
    args = parser.parse_args()
    utils.parse_options(args)
    utils.setup_logger(args)

    log.i("HPX START")

    if args.web and args.server:
        webserver.run(False)  # FIX: this is still blocking?
    elif args.web:
        webserver.run()

    if args.server:
        constants.available_commands = command.get_available_commands()
        constants.core_plugin = plugins._plugin_load(
            "happypanda.server.core.coreplugin", "core")

        if not args.safe:
            plugins.plugin_loader(constants.dir_plugin)
        else:
            plugins.registered.init_plugins()

        server.HPServer().run(interactive=args.interact)

    if constants.server_started:
        constants.config.save()
    log.i("HPX END")


if __name__ == '__main__':
    start()
