import os
import sys
import gipc

if __package__ is None and not hasattr(sys, 'frozen'):
    # direct call of main.py
    path = os.path.realpath(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(os.path.dirname(path)))

from happypanda.common import utils, constants, hlogger  # noqa: E402
from happypanda.core import server, plugins, command, views  # noqa: E402
from happypanda.core.commands import io_cmd  # noqa: E402

log = hlogger.Logger(__name__)
parser = utils.get_argparser()


def start():
    utils.setup_dirs()
    args = parser.parse_args()
    utils.parse_options(args)
    utils.setup_logger(args)

    if args.generate_config:
        constants.config.save()
        print("Generated configuration file at '{}'".format(io_cmd.CoreFS(constants.settings_file).path))
        return

    log.i("HPX SERVER START")

    if not args.only_web:
        constants.available_commands = command.get_available_commands()
        constants.core_plugin = plugins._plugin_load(
            "happypanda.core.coreplugin", "core", _logger=log)

        if not args.safe:
            plugins.plugin_loader(constants.dir_plugin)
        else:
            plugins.registered.init_plugins()

    log.i("Starting webserver... ({}:{})".format(constants.host_web, constants.port_web), stdout=True)
    web_args = (constants.host_web, constants.port_web, constants.dev if args.only_web else False)
    if args.only_web:
        server.WebServer().run(*web_args)
    else:
        gipc.start_process(server.WebServer().run, args=web_args, daemon=True)
        server.HPServer().run(interactive=args.interact)

    if not args.only_web:
        constants.config.save()
    log.i("HPX SERVER END")


if __name__ == '__main__':
    start()
