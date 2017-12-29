import os
import sys

if __package__ is None and not hasattr(sys, 'frozen'):
    # direct call of main.py
    path = os.path.realpath(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(os.path.dirname(path)))

import rollbar # noqa: E402
import multiprocessing  # noqa: E402

from gevent import monkey  # noqa: E402

from multiprocessing import Process  # noqa: E402
from apscheduler.triggers.interval import IntervalTrigger  # noqa: E402

from happypanda.common import utils, constants, hlogger, config  # noqa: E402
from happypanda.core import server, plugins, command, services, db  # noqa: E402
from happypanda.core.commands import io_cmd, meta_cmd  # noqa: E402

log = hlogger.Logger(__name__)
parser = utils.get_argparser()  # required to be at module lvl for sphinx.autoprogram ext


def start(argv=None, db_kwargs={}):
    #assert sys.version_info >= (3, 5), "Python 3.5 is required"
    e_code = None
    try:
        if argv is None:
            argv = sys.argv[1:]
        utils.setup_dirs()
        args = parser.parse_args(argv)
        utils.parse_options(args)

        if not args.only_web:
            db.init(**db_kwargs)
            command.init_commands()
            hlogger.Logger.init_listener(args)
            monkey.patch_all(thread=False)
        hlogger.Logger.report_online = config.report_critical_errors.value
        hlogger.Logger.setup_logger(args, main=True, debug=config.debug.value)
        utils.setup_online_reporter()
        log.i("HPX SERVER START")
        if constants.dev:
            log.i("DEVELOPER MODE ENABLED", stdout=True)
        log.i("\n{}".format(utils.os_info()))
        if args.gen_config:
            config.config.save_default()
            log.i("Generated example configuration file at {}".format(
                io_cmd.CoreFS(constants.config_example_path).path), stdout=True)
            return

        utils.setup_i18n()

        if not args.only_web:
            constants.available_commands = command.get_available_commands()

            services.init_generic_services()

            if not args.safe:
                plugins.plugin_loader(constants.dir_plugin)
            else:
                plugins.registered.init_plugins()

        constants.notification = server.ClientNotifications()

        upd_int = config.check_release_interval.value or config.check_release_interval.default
        upd_id = services.Scheduler.generic.add_command(meta_cmd.CheckUpdate(),
                                                    IntervalTrigger(minutes=upd_int))
        services.Scheduler.generic.start_command(upd_id, push=True)
        # starting stuff
        services.Scheduler.generic.start()
        log.i("Starting webserver... ({}:{})".format(config.host_web.value, config.port_web.value), stdout=True)
        web_args = (config.host_web.value, config.port_web.value, constants.dev if args.only_web else False)
        if args.only_web:
            server.WebServer().run(*web_args)
        else:
            constants.web_proc = Process(target=server.WebServer().run,
                                    args=web_args,
                                    kwargs={'logging_queue': hlogger.Logger._queue,
                                            'logging_args': args},
                                    daemon=True)
            constants.web_proc.start()
            hp_server = server.HPServer()
            meta_cmd.ShutdownApplication.shutdown.subscribe(hp_server.shutdown)
            meta_cmd.RestartApplication.restart.subscribe(hp_server.restart)
            meta_cmd.UpdateApplication.update.subscribe(hp_server.update)
            e_code = hp_server.run(interactive=args.interact)


        log.i("HPX SERVER END")
        if e_code == constants.ExitCode.Exit:
            log.i("Shutting down...", stdout=True)
        elif e_code == constants.ExitCode.Restart:
            log.i("Restarting...", stdout=True)
        if not args.only_web:
            config.config.save()
            hlogger.Logger.shutdown_listener()

        # the gui will handle the restart
        if e_code == constants.ExitCode.Restart and not constants.from_gui:
            utils.restart_process()
        elif e_code == constants.ExitCode.Update and not constants.from_gui:
            utils.launch_updater()

    except Exception as e:
        print(e) # intentional
        if config.report_critical_errors.value and not constants.dev:
            rollbar.report_exc_info()
        raise
    return e_code.value if e_code else 0

if __name__ == '__main__':
    multiprocessing.freeze_support()
    start()
