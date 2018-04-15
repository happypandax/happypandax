from gevent import monkey  # noqa: E402
# need to patch before importing requests, see
# https://github.com/requests/requests/issues/3752
monkey.patch_ssl()
monkey.patch_select()

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

import multiprocessing  # noqa: E402
import rollbar  # noqa: E402
import getpass  # noqa: E402

from multiprocessing import Process  # noqa: E402
from apscheduler.triggers.interval import IntervalTrigger  # noqa: E402
from happypanda.common import utils, constants, hlogger, config  # noqa: E402
from happypanda.core import server, plugins, command, services, db  # noqa: E402
from happypanda.core.commands import io_cmd, meta_cmd  # noqa: E402

log = hlogger.Logger(__name__)
parser = utils.get_argparser()  # required to be at module lvl for sphinx.autoprogram ext


def create_user_interactive():
    s = {}
    s['role'] = input("Which role should the user have?" +
                      "\n" + "(1) user (default)\t" +
                      "(2) guest\t" +
                      "(3) admin" +
                      "\nPlease input a number: ")
    s['role'] = {
        '1': db.User.Role.user,
        '2': db.User.Role.guest,
        '3': db.User.Role.admin}.get(
        s['role'],
        db.User.Role.user)
    print("Creating {}...".format(s['role'].value))
    s['username'] = utils.get_input(func=lambda: input("Username: "))
    if s['role'] != db.User.Role.guest:
        s['password'] = utils.get_input(func=getpass.getpass)
        if not s['password'] == getpass.getpass("Again: "):
            s = {}
            print("Passwords did not match")
    return s


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


def cmd_commands(args):
    if args.gen_config:
        config.config.save_default()
        log.i("Generated example configuration file at {}".format(
            io_cmd.CoreFS(constants.config_example_path).path), stdout=True)
        return True

    if args.create_user:
        print("============ Create User =============")
        uinfo = create_user_interactive()
        if uinfo:
            if db.create_user(uinfo['role'], uinfo['username'], uinfo.get("password", "")):
                print("Successfully created new user", uinfo['username'])
            else:
                print("User {} already exists".format(uinfo['username']))
        print("========== Create User End ===========")
        return True

    if args.delete_user:
        if db.delete_user(args.delete_user):
            print("Successfully deleted user", args.delete_user)
        else:
            print("User {} does not exist".format(args.delete_user))
        return True

    if args.list_users:
        for u in db.list_users(limit=20, offset=args.list_users - 1):
            print("{}\t{}".format(u.name, u.role.value))
        return True


def start(argv=None, db_kwargs={}):
    assert sys.version_info >= (3, 5), "Python 3.5 and up is required"
    e_code = None
    try:
        if argv is None:
            argv = sys.argv[1:]
        utils.setup_dirs()
        args = parser.parse_args(argv)
        utils.parse_options(args)
        db_inited = False

        if not args.only_web:
            db_inited = db.init(**db_kwargs)
            command.init_commands()
            monkey.patch_all(thread=False, ssl=False)
        else:
            db_inited = True

        if cmd_commands(args):
            return

        if not args.only_web:
            hlogger.Logger.init_listener(args)

        utils.setup_online_reporter()
        hlogger.Logger.setup_logger(args, main=True, debug=config.debug.value)
        utils.disable_loggers(config.disabled_loggers.value)

        log.i("HPX START")
        if constants.dev:
            log.i("DEVELOPER MODE ENABLED", stdout=True)
        log.i("\n{}".format(utils.os_info()))

        update_state = check_update() if not (not constants.is_frozen and constants.dev) else None

        if not update_state == constants.UpdateState.Installing.value and db_inited:

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
            if db_inited:
                e_code = constants.ExitCode.Update
            else:
                e_code = constants.ExitCode.Exit

        log.i("HPX END")

        if e_code == constants.ExitCode.Exit:
            log.i("Shutting down...", stdout=True)
        elif e_code == constants.ExitCode.Restart:
            log.i("Restarting...", stdout=True)
        if not args.only_web:
            config.config.save()
            hlogger.Logger.shutdown_listener()

        hlogger.shutdown()

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
