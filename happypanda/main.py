import os
import sys

if __package__ is None and not hasattr(sys, 'frozen'):
    # direct call of main.py
    path = os.path.realpath(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(os.path.dirname(path)))

from happypanda.common import utils, constants, hlogger  # noqa: E402
from happypanda.core import server, plugins, command  # noqa: E402

log = hlogger.Logger(__name__)


def start():
    utils.setup_dirs()
    parser = utils.get_argparser()
    args = parser.parse_args()
    utils.parse_options(args)
    utils.setup_logger(args)

    log.i("HPX SERVER START")

    constants.available_commands = command.get_available_commands()
    constants.core_plugin = plugins._plugin_load(
        "happypanda.core.coreplugin", "core", _logger=log)

    if not args.safe:
        plugins.plugin_loader(constants.dir_plugin)
    else:
        plugins.registered.init_plugins()

    server.HPServer().run(interactive=args.interact)

    constants.config.save()
    log.i("HPX SERVER END")


if __name__ == '__main__':
    start()
