# flake8: noqa
import os
import sys
import shutil
import argparse
import subprocess
import zipfile
import pathlib
from subprocess import run
from importlib import reload

dev_options = dict(
    build_db=123,
    prev_build=None,
    env_activated=False
)

env_python = r".\env\Scripts\python" if sys.platform.startswith("win") else "./env/bin/python"

changes = """
Refer to release changelog
"""


def question(question, default="yes"):
    """Ask a yes/no question via raw_input() and return their answer.

    "question" is a string that is presented to the user.
    "default" is the presumed answer if the user just hits <Enter>.
        It must be "yes" (the default), "no" or None (meaning
        an answer is required of the user).

    The "answer" return value is True for "yes" or False for "no".
    """
    valid = {"yes": True, "y": True, "ye": True,
             "no": False, "n": False}
    if default is None:
        prompt = " [y/n] "
    elif default == "yes":
        prompt = " [Y/n] "
    elif default == "no":
        prompt = " [y/N] "
    else:
        raise ValueError("invalid default answer: '%s'" % default)

    while True:
        sys.stdout.write(question + prompt)
        choice = input().lower()
        if default is not None and choice == '':
            return valid[default]
        elif choice in valid:
            return valid[choice]
        else:
            sys.stdout.write("Please respond with 'yes' or 'no' "
                             "(or 'y' or 'n').\n")


def is_tool(name):
    return shutil.which(name)


def is_installed(cmd):
    _cmd = cmd
    if not is_tool(cmd):
        print("Seems like '{}' is not in your PATH".format(_cmd))
        if question("Can you supply an alternative?"):
            _cmd = input("Please enter path to the {} script/executable".format(_cmd))
        else:
            print("Cannot continue. Please make sure '{}' is available, or setup HPX manually".format(_cmd))
            sys.exit(1)
    return _cmd


def build(args, unknown=None):
    _activate_venv()
    if getattr(args, 'client', False):
        try:
            import build_webclient
        except ImportError:
            print("Please supply the '--dev' argument if you want to build the webclient")
            sys.exit(1)

        print("Building webclient")
        build_webclient.main(unknown)

    if getattr(args, 'docs', False):
        try:
            import build_docs
        except ImportError:
            print("Please supply the '--dev' argument if you want to build the docs")
            sys.exit(1)

        print("Building docs")
        build_docs.main()

    print(
        "\nLast build requiring a db rebuild: {}\nPlease use the accompanying script 'HPtoHPX.py' to rebuild your database just once if you've surpassed this build".format(
            dev_options['build_db']))


def _activate_venv():
    if os.environ.get('CI'):
        return

    if not dev_options['env_activated']:
        if not os.path.exists('env'):
            print("Looks like you haven't installed HPX yet. Please run '$ python bootstrap.py install' to install")

        scripts = os.path.join("env", "Scripts")
        if not os.path.exists(scripts):
            scripts = os.path.join("env", "bin")

        print("Activating virtualenv")
        activator = os.path.join(scripts, "activate_this.py")
        with open(activator) as f:
            exec(f.read(), {'__file__': activator})
        dev_options['env_activated'] = True


def _check_python():
    _cmd = "python3"
    install_cmd_stuff = True
    if not is_installed(_cmd):
        print("Seems like '{}' is not in your PATH".format(_cmd))
        if question("Can you supply an alternative?"):
            _cmd = input("Please enter path to the {} script/executable".format(_cmd))
        else:
            install_cmd_stuff = False
            print("Cannot continue. Please make sure '{}' is available, or setup HPX manually".format(_cmd))
            sys.exit()
    return _cmd


def _check_pip():
    print("Checking for pip")
    try:
        import pip
    except ImportError:
        print("Seems like pip is not installed. Please install pip to continue")
        sys.exit(1)


def _update_pip(args, skip=True):
    if not args.dev and skip:
        try:
            from happypanda import main
            return
        except ImportError:
            pass
    print("Installing required packages...")
    r = "requirements.txt" if not args.dev else "requirements-dev.txt"
    env_p = r".\env\Scripts\pip3" if sys.platform.startswith("win") else "./env/bin/pip3"
    run([env_p, "install", "-r", r])


def install(args):
    print("Installing HPX...")
    _check_pip()

    try:
        import virtualenv
        import pip
    except ImportError:
        print("Installing virtualenv")
        import pip
        pip.main(["install", "virtualenv"])
        print("Please re-run bootstrap.py install")
        sys.exit()

    if not os.path.exists("env"):
        print("Setting up virtualenv")

        virtualenv.create_environment("env")

    scripts = os.path.join("env", "Scripts")
    if not os.path.exists(scripts):
        scripts = os.path.join("env", "bin")

    _activate_venv()

    _update_pip(args)

    print("Finished installing.")
    if args.run:
        build(args)


def update(args):
    if args.packages:
        _activate_venv()
        _update_pip(args, False)
    else:
        cmd = is_installed("git")
        if not os.path.exists(".git"):
            if not question("Looks like we're not connected to the main repo. Do you want me to set it up for you?"):
                sys.exit(1)
            print("Setting up git repo...")
            run([cmd, "init", "."])
            run([cmd, "remote", "add", "-f", "origin", "https://github.com/happypandax/server.git"])
        b = "dev"
        run([cmd, "checkout", b, "-f"])

        _activate_venv()
        from happypanda.common import constants
        dev_options['prev_build'] = constants.build
        print("Pulling changes...")
        run([cmd, "pull"])
        constants = reload(constants)
        build(args)
        version(args)


def version(args):
    _activate_venv()
    from happypanda.common import constants
    if args.app_version:
        print(constants.version_str)
        return
    if args.app_release:
        print("HappyPanda X " + ('PREVIEW ' if constants.preview else '') + 'v' + constants.version_str)
        return

    print("\n-----------------------------------------------\n")
    if dev_options['prev_build']:
        print("Build: {} -> {}".format(dev_options['prev_build'], constants.build))
    else:
        print("Build: {}".format(constants.build))

    import bootstrap
    print("\n------------------- Changes -------------------")
    print(bootstrap.changes)
    print(
        "\nLast build requiring a db rebuild: {}\nPlease use the accompanying script 'HPtoHPX.py' to rebuild your database just once if you've surpassed this build".format(
            dev_options['build_db']))


def convert(args, unknown=None):
    _activate_venv()
    print("Convert HP database to HPX database")
    try:
        from HPtoHPX import main
    except ImportError:
        _update_pip(args)
    argv = []
    argv.append(args.db_path)
    data_folder = "data"
    if not os.path.isdir(data_folder):
        os.makedirs(data_folder)
    argv.append(os.path.join("data", "happypanda_dev.db" if args.dev else "happypanda.db"))
    argv.extend(sys.argv[3:])
    for i in ("-d", "--dev"):
        try:
            argv.remove(i)
        except ValueError:
            pass
    return run([env_python, "HPtoHPX.py", *argv]).returncode


def is_sane_database(Base, session):
    """Check whether the current database matches the models declared in model base.
    Currently we check that all tables exist with all columns. What is not checked
    * Column types are not verified
    * Relationships are not verified at all (TODO)
    :param Base: Declarative Base for SQLAlchemy models to check
    :param session: SQLAlchemy session bound to an engine
    :return: True if all declared models have corresponding tables and columns.
    """

    engine = session.get_bind()
    iengine = inspect(engine)

    errors = False

    tables = iengine.get_table_names()

    # Go through all SQLAlchemy models
    for name, klass in Base._decl_class_registry.items():

        if isinstance(klass, _ModuleMarker):
            # Not a model
            continue

        table = klass.__tablename__
        if table in tables:
            # Check all columns are found
            # Looks like [{'default': "nextval('sanity_check_test_id_seq'::regclass)",
            # 'autoincrement': True, 'nullable': False, 'type': INTEGER(), 'name':
            # 'id'}]

            columns = [c["name"] for c in iengine.get_columns(table)]
            mapper = inspect(klass)

            for column_prop in mapper.attrs:
                if isinstance(column_prop, RelationshipProperty):
                    # TODO: Add sanity checks for relations
                    pass
                else:
                    for column in column_prop.columns:
                        # Assume normal flat column
                        if not column.key in columns:
                            logger.error(
                                "Model %s declares column %s which does not exist in database %s",
                                klass,
                                column.key,
                                engine)
                            errors = True
        else:
            logger.error("Model %s declares table %s which does not exist in database %s", klass, table, engine)
            errors = True

    return not errors


def _check_db(args):
    from sqlalchemy import inspect
    from sqlalchemy.ext.declarative.clsregistry import _ModuleMarker
    from sqlalchemy.orm import RelationshipProperty


def start(args, unknown=None):
    _activate_venv()
    try:
        from happypanda import main
    except ImportError:
        _update_pip(args)
    return run([env_python, "run.py", *sys.argv[2:]]).returncode


def test(args, unknown=None):
    _activate_venv()
    try:
        from run_tests import main
    except ImportError:
        _update_pip(args)
    return main(sys.argv[2:], False, env_python)


def lint(args, unknown=None):
    _activate_venv()
    return run([env_python, "lint.py", *sys.argv[2:]]).returncode


def migrate_revision(args, unk=None):
    _activate_venv()
    d_a = []
    if args.dev:
        d_a += ['-x', 'dev=true']
    return run(["alembic", *d_a, "revision", "-m", getattr(args, "msg", "new version"), "--autogenerate"]).returncode


def migrate_upgrade(args, unk=None):
    _activate_venv()
    d_a = []
    if args.dev:
        d_a += ['-x', 'dev=true']
    return run(["alembic", *d_a, "upgrade", args.rev]).returncode


def _compress_dir(dir_path, output_name, fmt="zip"):
    from happypanda.common import config
    print("Compressing {} archive...".format(fmt))
    if fmt == "7z":
        s7path = config.sevenzip_path.value
        if os.environ.get('APPVEYOR'):
            s7path = "7z.exe"

        if not s7path:
            print("Please set the path to the 7z executable in your configuration (advanced -> 7z_path)")
            sys.exit(1)

        return run([s7path, "a", output_name, os.path.join(dir_path, "*")])
    else:
        p = shutil.make_archive(dir_path, fmt, dir_path)
        os.replace(p, output_name)


def _osx_installer(app_path, volume_name, output_name):
    print("Creating OS X installer...")
    setting_file = os.path.join(".", "deploy", "osx", "dmgbuild_settings.py")
    return run(["dmgbuild", "-s", setting_file, '-D',
                "app={}".format(os.path.abspath(app_path)),
                '"{}"'.format(volume_name),
                os.path.abspath(output_name)])


def deploy(args, unknown=None):
    _activate_venv()
    try:
        from PyInstaller.__main__ import run as prun
    except ImportError:
        if not args.dev:
            print("Please supply the '--dev' argument if you want to deploy")
            sys.exit(1)
        else:
            _update_pip(args)
        from PyInstaller.__main__ import run as prun

    import happypanda.core.command
    from happypanda.common import constants
    from happypanda.core import updater

    if not args.dev:
        args.client = True
        build(args, ["--prod"])
        run([is_tool(is_installed("npm")), "run", "build"])

    if constants.is_osx:
        os_name = "osx"
    elif constants.is_win:
        os_name = "win"
    elif constants.is_linux:
        os_name = "linux"

    sha_file_o = os.path.join(".", "dist", "sha256.txt")
    output_path = os.path.join(".", "dist", "happypandax")
    updater_path = "dist"
    dir_path = os.path.join(".", "dist", "happypandax")
    if constants.is_osx:
        dir_path = os.path.join(dir_path, constants.osx_bundle_name, "Contents", "MacOS")
    installer_filename = ".installed"
    installer_file = os.path.join("deploy", installer_filename)
    if not prun(["happypandax.spec", "--noconfirm"]) and not prun(['updater.py',
                                                                   '--onefile',
                                                                   '--name',
                                                                   constants.updater_name,
                                                                   '--icon',
                                                                   constants.favicon_path,
                                                                   '--specpath',
                                                                   'build'
                                                                   ]):
        upd_name = constants.updater_name
        if constants.is_win:
            upd_name += '.exe'

        if constants.is_osx:
            bundle_path_old = os.path.join("dist", constants.osx_bundle_name)
            bundle_path = os.path.join(output_path, constants.osx_bundle_name)
            os.replace(bundle_path_old, bundle_path)
        os.replace(os.path.join(updater_path, upd_name), os.path.join(dir_path, upd_name))

        if os.environ.get('CI'):
            deploy_dir = os.path.join("dist", "files")
            if os.path.exists(deploy_dir):
                shutil.rmtree(deploy_dir)
            os.mkdir(deploy_dir)

        for p in ("", "installer"):
            if constants.preview:
                output_path_a = output_path + ".PREVIEW."
            output_path_a = output_path + ".".join(str(x) for x in constants.version)
            output_path_a = output_path_a + "." + os_name
            if p:
                output_path_a = output_path_a + "." + p

            installer_file_out = os.path.join(dir_path, installer_filename)
            if p == "installer":
                if constants.is_linux:
                    continue
                if not os.path.exists(installer_file_out):
                    shutil.copyfile(installer_file, installer_file_out)
            else:
                if os.path.exists(installer_file_out):
                    os.remove(installer_file_out)

            fmt = 'zip' if constants.is_win else 'gztar'
            if p == 'installer' and constants.is_win:
                fmt = '7z'
            elif p == 'installer' and constants.is_osx:
                fmt = 'dmg'

            output_path_a = output_path_a + '.' + ((fmt[2:] + '.' + fmt[:2]) if 'tar' in fmt else fmt)
            if os.path.exists(output_path_a):
                os.remove(output_path_a)

            if p == 'installer' and constants.is_osx:
                _osx_installer(bundle_path, os.path.splitext(constants.osx_bundle_name)[0],
                               output_path_a)
            else:
                _compress_dir(output_path, output_path_a, fmt)

            if p != "installer":
                sha_value = updater.sha256_checksum(output_path_a)
                with open(sha_file_o, "w") as f:
                    f.write(sha_value)
                print("{}\n\tSHA256 Checksum: {}".format(output_path_a, sha_value))

            if os.environ.get('CI'):
                deploy_file_o = os.path.join(deploy_dir, pathlib.Path(output_path_a).name)
                try:
                    os.replace(output_path_a, deploy_file_o)
                except FileNotFoundError as e:
                    print(e)

    print("Done")


def file_checksum(args, u=None):
    _activate_venv()
    from happypanda.core import updater
    print("{}\n\tSHA256 Checksum: {}".format(args.f, updater.sha256_checksum(args.f)))


welcome_msg = """
Welcome to HPX development helper script.

HPX requires Python 3.5. Make sure that Python version is installed and in use.
If this is your first time running this script, or if you haven't installed HPX yet, run:
    $ python3 bootstrap.py install
Other optional downloads are:
    - Git: If you want to automagically fetch new changes.
    - NodeJS: If you want to work on the webclient.

As of this build HPX does not implement any write features, and so you need a HP database to use HPX.
Convert it using the following command:
    $ python3 bootstrap.py convert <path-to-old-HP-db>

You can now start HPX by running the following command (additional arguments will be forwarded):
    $ python3 bootstrap.py run

You only need to install once. After installing, you can update HPX after pulling the new changes from the git repo by running:
    $ python3 bootstrap.py build

Or, to automatically pull the changes and build for you, just run (make sure you have git installed):
    $ python3 bootstrap.py update

Finally, each action may have additional optional arguments. Make sure to check them out by supplying "--help" after the action:
    $ python3 bootstrap.py build --help

For example, to build the webclient or docs, run:
    $ python3 bootstrap.py build --client --docs

To see all actions, run:
    $ python3 bootstrap.py help

---- Webclient ----

You need NodeJS installed to work on the webclient.
Start by installing the dependencies:
    $ npm install

Work on the webclient (files are located at './templates/' and './semantic/src/').
To build the python files run:
    $ python3 bootstrap.py build --client
and then bundle everything together by running:
    $ npm run build-dev

Lastly, compile the CSS files by running:
    $ cd ./semantic
    $ gulp build-css build-assets

I should probably do something about this needlessly complicated and tedious process...

Happy coding!

Scroll up if you can't read everything!
"""


def main():

    parser = argparse.ArgumentParser(description="A helping script for setting up HPX")
    parser.add_argument('-d', '--dev', action='store_true', help="Enable dev mode")
    parser.set_defaults(func=lambda args: print(welcome_msg))
    subparsers = parser.add_subparsers(description='Specify an action before "--help" to show parameters for it.',
                                       metavar='ACTION', dest='action')

    subparser = subparsers.add_parser('build', help='Build HPX')
    subparser.add_argument('--docs', action='store_true', help="Build docs")
    subparser.add_argument('--client', action='store_true', help="Build webclient")
    subparser.set_defaults(func=build)

    subparser = subparsers.add_parser('install', help='Install HPX')
    subparser.add_argument('--run', action='store_true', help="Run HPX after installing")
    subparser.set_defaults(func=install)

    subparser = subparsers.add_parser('lint', help='Linting, args are forwarded')
    subparser.set_defaults(func=lint)

    subparser = subparsers.add_parser('migrate', help='Migration tool')
    subparser.add_argument('-d', '--dev', action='store_true', help="dev mode")
    subparser.set_defaults(func=migrate_revision)
    subsubparsers = subparser.add_subparsers(description='Specify an action before "--help" to show parameters for it.',
                                             metavar='ACTION', dest='action')
    subsubparser = subsubparsers.add_parser('revision', help='Add a new revision')
    subsubparser.set_defaults(func=migrate_revision)
    subsubparser.add_argument('msg', help="revision message")
    subsubparser.add_argument('-d', '--dev', action='store_true', help="dev mode")

    subsubparser = subsubparsers.add_parser('upgrade', help='Upgrade to a revision')
    subsubparser.set_defaults(func=migrate_upgrade)
    subsubparser.add_argument('rev', help="revision", default="head", nargs="?")
    subsubparser.add_argument('-d', '--dev', action='store_true', help="dev mode")

    subparser = subparsers.add_parser('deploy', help='Deploy on current platform')
    subparser.set_defaults(func=deploy)

    subparser = subparsers.add_parser('hash', help='Generate SHA-256 hash of given file')
    subparser.add_argument('f', help="filepath")
    subparser.set_defaults(func=file_checksum)

    subparser = subparsers.add_parser('update', help='Fetch the latest changes from the GitHub repo')
    subparser.set_defaults(func=update)
    subparser.add_argument('-p', '--packages', action='store_true', help="Update pip packages")
    subparser.add_argument('-d', '--dev', action='store_true', help="Update pip packages from `requirements-dev.txt`")

    subparser = subparsers.add_parser(
        'convert', help='Convert HP database to HPX database, additional args will be passed to `HPtoHPX.py`')
    subparser.add_argument('db_path', help="Path to old HP database file")
    subparser.add_argument('-d', '--dev', action='store_true', help="Convert to ´happypanda_dev.db´ instead")
    subparser.set_defaults(func=convert)

    subparser = subparsers.add_parser('version', help='Display build number and latest changes')
    subparser.add_argument('--app-version', action='store_true', help="Current app version")
    subparser.add_argument('--app-release', action='store_true', help="Current app release name")
    subparser.set_defaults(func=version)

    subparser = subparsers.add_parser('run', help='Start HPX, additional args will be passed to HPX')
    subparser.set_defaults(func=start)

    subparser = subparsers.add_parser('test', help='Run tests, additional args are passed to pytest')
    subparser.set_defaults(func=test)

    subparser = subparsers.add_parser('help', help='Help')
    subparser.set_defaults(func=lambda a: parser.print_help())

    if any([x in sys.argv for x in ("run", "convert", "lint", "build", "test")]):
        a = args, unknown = parser.parse_known_args()
    else:
        a = args = parser.parse_args()
        a = (a,)
    return args.func(*a)


if __name__ == '__main__':
    sys.exit(main())
