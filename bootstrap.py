import os
import sys
import argparse
import subprocess
from subprocess import run
from importlib import reload

dev_options = dict(
    build_db = False,
    )

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
    try:
        devnull = open(os.devnull)
        subprocess.Popen([name], stdout=devnull, stderr=devnull).communicate()
    except OSError as e:
        if e.errno == os.errno.ENOENT:
            return False
    return True

def is_installed(cmd):
    _cmd = cmd
    if not is_tool(cmd):
        print("Seems like '{}' is not in your PATH".format(_cmd))
        if question("Can you supply an alternative?"):
            _cmd = input("Please enter path to the {} script/executable".format(_cmd))
        else:
            print("Cannot continue. Please make sure '{}' is available, or setup HPX manually".format(_cmd))
            sys.exit()
    return _cmd

def build(args):
    _activate_venv()
    _update_pip(args)

    if args.client:
        try:
            import build_webclient
        except ImportError:
            print("Please supply the '--dev' argument if you want to build the webclient")

        print("Building webclient")
        build_webclient.main()

    if args.docs:
        try:
            import build_webclient
        except ImportError:
            print("Please supply the '--dev' argument if you want to build the docs")

        print("Building docs")
        build_docs.main()

    if dev_options['build_db']:
        print("\n# IMPORTANT # A database rebuild is required for this build, please use the accompanying script 'HPtoHPX.py' to rebuild your database if you've just updated")

def _activate_venv():
    if not os.path.exists('env'):
        print("Looks like you haven't installed HPX yet. Please run '$ python bootstrap.py install' to install")

    scripts = os.path.join("env", "Scripts")
    if not os.path.exists(scripts):
        scripts = os.path.join("env", "bin")

    print("Activating virtualenv")
    activator = os.path.join(scripts, "activate_this.py")
    with open(activator) as f:
        exec(f.read(), {'__file__': activator})

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
        sys.exit()

def _update_pip(args):
    print("Installing required packages...")
    r = "requirements.txt" if not args.dev else "requirements-dev.txt"
    run(["pip3", "install", "-r", r, "--upgrade"])

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
        import virtualenv

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
    cmd = is_installed("git")
    if not os.path.exists(".git"):
        if not question("Looks like we're not connected to the main repo. Do you want me to set it up for you?"):
            sys.exit()
        print("Setting up git repo...")
        run([cmd, "init", "."])
        run([cmd, "remote", "add", "-f", "origin", "https://github.com/happypandax/server.git"])
        b = "dev" if args.dev else "master"
        run([cmd, "checkout", b, "-f"])

    print("Pulling changes...")
    run([cmd, "pull"])
    build(args)

def start(args):
    _activate_venv()
    try:
        from happypanda import main
    except ImportError:
        _update_pip(args)
    env_p = r".\env\Scripts\python" if sys.platform.startswith("win") else "env/bin/python"
    return run([env_p, "run.py", *sys.argv[2:]], shell=True).returncode

welcome_msg = """
Welcome to HPX development helper script.

If this is your first time running this script, or if you haven't installed HPX yet, run:
    $ python3 bootstrap.py install
HPX requires Python 3.5 and optionally npm to build the webclient and git to fetch new changes.
Make sure those are installed before running the command above.

You can now start HPX by running:
    $ python3 bootstrap.py run

You only need to install once. After installing, you can update HPX after pulling the new changes from the git repo by running:
    $ python3 bootstrap.py build

To automatically pull the changes and build for you, just run:
    $ python3 bootstrap.py update

Finally, each action may have additional optional arguments. Make sure to check them out by supplying "--help" after the action:
    $ python3 bootstrap.py build --help
    
For example, to build the webclient or docs, run:
    $ python3 bootstrap.py build --client --docs

To see all actions, run:
    $ python3 bootstrap.py help

Happy coding!
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

    subparser = subparsers.add_parser('update', help='Fetch the latest changes from the GitHub repo')
    subparser.set_defaults(func=update)

    subparser = subparsers.add_parser('run', help='Start HPX, additional args will be passed to HPX')
    subparser.set_defaults(func=start)

    subparser = subparsers.add_parser('help', help='Help')
    subparser.set_defaults(func=lambda a: parser.print_help())

    if 'run' in sys.argv:
        args, unknown = parser.parse_known_args()
    else:
        args = parser.parse_args()
    return args.func(args)

if __name__ == '__main__':
    sys.exit(main())