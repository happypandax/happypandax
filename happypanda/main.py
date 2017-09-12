import os
import sys

if __package__ is None and not hasattr(sys, 'frozen'):
    # direct call of main.py
    path = os.path.realpath(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(os.path.dirname(path)))

from gevent import monkey  # noqa: E402

from multiprocessing import Process  # noqa: E402

from happypanda.common import utils, constants, hlogger  # noqa: E402
# views need to be imported before starting the webserver in a different process
from happypanda.core.web import views  # noqa: F401
from happypanda.core import server, plugins, command, services, db  # noqa: E402
from happypanda.core.commands import io_cmd  # noqa: E402

log = hlogger.Logger(__name__)


def start(argv=None, db_kwargs={}):
    if argv is None:
        argv = sys.argv[1:]
    parser = utils.get_argparser()
    utils.setup_dirs()
    args = parser.parse_args(argv)
    utils.parse_options(args)

    if not args.only_web:
        db.init(**db_kwargs)
        command.init_commands()
        hlogger.Logger.init_listener(args)
        monkey.patch_all(thread=False)

    hlogger.Logger.setup_logger(args)

    if args.generate_config:
        constants.config.save()
        log.i("Generated configuration file at '{}'".format(io_cmd.CoreFS(constants.settings_file).path), stdout=True)
        return

    log.i("HPX SERVER START")

    if not args.only_web:
        constants.available_commands = command.get_available_commands()

        services.init_generic_services()

        if not args.safe:
            plugins.plugin_loader(constants.dir_plugin)
        else:
            plugins.registered.init_plugins()

    log.i("Starting webserver... ({}:{})".format(constants.host_web, constants.port_web), stdout=True)
    web_args = (constants.host_web, constants.port_web, constants.dev if args.only_web else False)
    if args.only_web:
        server.WebServer().run(*web_args)
    else:
        Process(target=server.WebServer().run,
                args=web_args,
                kwargs={'logging_queue': hlogger.Logger._queue,
                        'logging_args': args},
                daemon=True).start()
        server.HPServer().run(interactive=args.interact)

    if not args.only_web:
        constants.config.save()
        hlogger.Logger.shutdown_listener()
    log.i("HPX SERVER END")

if __name__ == '__main__':
    start()
