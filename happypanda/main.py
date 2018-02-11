import os
import sys

if __package__ is None and not hasattr(sys, 'frozen'):
    # direct call of main.py
    path = os.path.realpath(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(os.path.dirname(path)))

# OS X: fix the working directory when running a mac app
# OS X: files are in [app]/Contents/MacOS/
# WIN: fix working directoy when added to start at boot
if hasattr(sys, 'frozen'):
    os.chdir(os.path.abspath(os.path.dirname(sys.executable)))


from gevent import monkey  # noqa: E402
if __name__ == '__main__':
    # need to patch before importing requests, see
    # https://github.com/requests/requests/issues/3752
    monkey.patch_ssl()

import multiprocessing  # noqa: E402
import rollbar  # noqa: E402

from multiprocessing import Process  # noqa: E402
from apscheduler.triggers.interval import IntervalTrigger  # noqa: E402
from happypanda.common import utils, constants, hlogger, config  # noqa: E402
from happypanda.core import server, plugins, command, services, db  # noqa: E402
from happypanda.core.commands import io_cmd, meta_cmd  # noqa: E402

log = hlogger.Logger(__name__)
parser = utils.get_argparser()  # required to be at module lvl for sphinx.autoprogram ext


def check_update():
    with utils.intertnal_db() as db:
        update_info = db.get(constants.updater_key, {})

    state = None
    if update_info:
        if update_info['state'] == constants.UpdateState.Registered.value:
            update_info['state'] = constants.UpdateState.Installing.value
            with utils.intertnal_db() as db:
                db[constants.updater_key] = update_info
            state = constants.UpdateState.Installing.value
        else:
            with utils.intertnal_db() as db:
                db[constants.updater_key] = {}
            if not update_info['state'] == constants.UpdateState.Installing.value:
                state = update_info['state']
    return state


def start(argv=None, db_kwargs={}):
    assert sys.version_info >= (3, 5), "Python 3.5 and up is required"
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
            monkey.patch_all(thread=False, ssl=False)
        utils.setup_online_reporter()
        hlogger.Logger.setup_logger(args, main=True, debug=config.debug.value)
        log.i("HPX START")
        if constants.dev:
            log.i("DEVELOPER MODE ENABLED", stdout=True)
        log.i("\n{}".format(utils.os_info()))
        if args.gen_config:
            config.config.save_default()
            log.i("Generated example configuration file at {}".format(
                io_cmd.CoreFS(constants.config_example_path).path), stdout=True)
            return

        update_state = check_update()

        if not update_state == constants.UpdateState.Installing.value:

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
                                                     'cmd_args': args},
                                             daemon=True)
                constants.web_proc.start()
                hp_server = server.HPServer()
                meta_cmd.ShutdownApplication.shutdown.subscribe(hp_server.shutdown)
                meta_cmd.RestartApplication.restart.subscribe(hp_server.restart)
                meta_cmd.UpdateApplication.update.subscribe(hp_server.update)
                e_code = hp_server.run(interactive=args.interact)

            io_cmd.CoreFS(constants.dir_temp).delete(ignore_errors=True)

        else:
            e_code = constants.ExitCode.Update

        log.i("HPX END")

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
        if constants.web_proc:
            constants.web_proc.terminate()
        print(e)  # intentional
        if config.report_critical_errors.value and not constants.dev and constants.is_frozen:
            rollbar.report_exc_info()
        raise
    return e_code.value if e_code else 0


if __name__ == '__main__':
    multiprocessing.freeze_support()
    start()
