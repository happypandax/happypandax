import os  # noqa: E402
import sys  # noqa: E402
import rollbar  # noqa: E402
import getpass  # noqa: E402
import pdb
#import faulthandler
#f = open("fault.log", "w")
# faulthandler.enable(f)
#faulthandler.dump_traceback_later(120, repeat=True, file=f)

# OS X: fix the working directory when running a mac app
# OS X: files are in [app]/Contents/MacOS/
# WIN: fix working directoy when added to start at boot
if hasattr(sys, 'frozen'):
    os.chdir(os.path.abspath(os.path.dirname(sys.executable)))

from multiprocessing import Process  # noqa: E402
from apscheduler.triggers.interval import IntervalTrigger  # noqa: E402

from happypanda.common import utils, constants, hlogger, config, exceptions  # noqa: E402
from happypanda.core import server, plugins, command, services, db, async_utils  # noqa: E402
from happypanda.core.commands import io_cmd, meta_cmd  # noqa: E402

log = hlogger.Logger(__name__)
parser = utils.get_argparser()  # required to be at module lvl for sphinx.autoprogram ext
async_utils.patch_psycopg()


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
    update_info = constants.internaldb.get(constants.updater_key, {})

    state = None
    if update_info:
        if update_info['state'] == constants.UpdateState.Registered.value:
            update_info['state'] = constants.UpdateState.Installing.value
            constants.internaldb[constants.updater_key] = update_info
            state = constants.UpdateState.Installing.value
        else:
            constants.internaldb[constants.updater_key] = {}
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
            print("{}\t[{}]".format(u.name, u.role.value))
        return True


def init_commands(args):
    if not args.only_web:
        upd_int = config.check_release_interval.value or config.check_release_interval.default
        upd_id = services.Scheduler.generic.add_command(meta_cmd.CheckUpdate(),
                                                        IntervalTrigger(minutes=upd_int))
        log.i("Initiating background", meta_cmd.CheckUpdate.__name__)
        services.Scheduler.generic.start_command(upd_id, push=True)

        log.i("Initiating background thumbnail", io_cmd.CacheCleaner.__name__)
        thumb_id = services.TaskService.generic.add_command(io_cmd.CacheCleaner())
        constants.task_command.thumbnail_cleaner = services.TaskService.generic.start_command(
            thumb_id, constants.dir_thumbs, size=config.auto_thumb_clean_size.value, silent=True)

        log.i("Initiating background temp", io_cmd.CacheCleaner.__name__)
        temp_id = services.TaskService.generic.add_command(io_cmd.CacheCleaner())
        constants.task_command.temp_cleaner = services.TaskService.generic.start_command(
            temp_id, constants.dir_temp, size=config.auto_temp_clean_size.value, silent=True)


def start(argv=None, db_kwargs={}):
    assert sys.version_info >= (3, 6), "Python 3.6 and up is required"
    e_code = None
    e_num = 0
    try:
        utils.setup_online_reporter()
        log.i("HPX START")
        log.i("Version:", constants.version_str)
        log.i("DB Version:", constants.version_db_str)
        log.i("Web Version:", constants.version_web_str)
        if argv is None:
            argv = sys.argv[1:]
        utils.setup_dirs()
        args = parser.parse_args(argv)
        utils.parse_options(args)
        # setup logger without multiprocessing
        hlogger.Logger.setup_logger(args, main=True, dev=constants.dev, debug=config.debug.value)
        utils.enable_loggers(config.enabled_loggers.value)
        db_inited = False
        if constants.dev:
            log.i("DEVELOPER MODE ENABLED", stdout=True)
        else:
            pdb.set_trace = lambda: None  # disable pdb
        if config.debug.value:
            log.i("DEBUG MODE ENABLED", stdout=True)
        log.i(utils.os_info())

        if not args.only_web:
            db_inited = db.init(**db_kwargs)
            command.setup_commands()
        else:
            db_inited = True

        if cmd_commands(args):
            return

        if not args.only_web:  # can't init earlier because of cmd_commands
            hlogger.Logger.init_listener(args=args, debug=config.debug.value, dev=constants.dev)

        # setup logger with multiprocessing
        hlogger.Logger.setup_logger(
            args,
            main=True,
            dev=constants.dev,
            debug=config.debug.value,
            logging_queue=hlogger.Logger._queue)

        update_state = check_update() if not (not constants.is_frozen and constants.dev) else None

        if not update_state == constants.UpdateState.Installing.value and db_inited:

            utils.setup_i18n()

            if not args.only_web:
                constants.available_commands = command.get_available_commands()

                services.setup_generic_services()

                constants.plugin_manager = plugins.PluginManager()

                if not args.safe:
                    plugins.plugin_loader(constants.plugin_manager, constants.dir_plugin)
                    if config.plugin_dir.value:
                        plugins.plugin_loader(constants.plugin_manager, config.plugin_dir.value)

            constants.notification = server.ClientNotifications()

            # starting stuff
            services.Scheduler.generic.start()
            init_commands(args)

            log.i("Starting webserver... ({}:{})".format(config.host_web.value, config.port_web.value), stdout=True)
            web_args = (config.host_web.value, config.port_web.value)
            web_kwargs = {
                'dev': constants.dev,
                'debug': config.debug.value,
            }
            if args.only_web:
                server.WebServer().run(*web_args, **web_kwargs)
            else:
                web_kwargs.update({'logging_queue': hlogger.Logger._queue,
                                   'cmd_args': args, })
                constants.web_proc = Process(target=server.WebServer().run,
                                             args=web_args,
                                             kwargs=web_kwargs,
                                             daemon=True,
                                             name="gevent")
                constants.web_proc.start()
                hp_server = server.HPServer()
                meta_cmd.ShutdownApplication.shutdown.subscribe(hp_server.shutdown)
                meta_cmd.RestartApplication.restart.subscribe(hp_server.restart)
                meta_cmd.UpdateApplication.update.subscribe(hp_server.update)
                e_code = hp_server.run(interactive=args.interact)

        else:
            if db_inited:
                e_code = constants.ExitCode.Update
            else:
                e_code = constants.ExitCode.Exit

        io_cmd.CoreFS(constants.dir_temp).delete(ignore_errors=True)
        log.i("HPX END")

        if e_code == constants.ExitCode.Exit:
            log.i("Shutting down...", stdout=True)
        elif e_code == constants.ExitCode.Restart:
            log.i("Restarting...", stdout=True)
        if not args.only_web:
            config.config.save()
            services.Scheduler.shutdown_all()
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
        e_num = 1
        if not isinstance(e, exceptions.CoreError):
            if config.report_critical_errors.value and not constants.dev and constants.is_frozen:
                rollbar.report_exc_info()
            raise
    return e_code.value if e_code else e_num
