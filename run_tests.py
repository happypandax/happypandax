from sys import exit, argv, executable
from os import chdir, path
from subprocess import run

def main(args=None, sysexit=True, executable=executable):
    # Change current working directory. This makes it so run_tests.py is
    # required to be on the same level as the happypanda folder
    chdir(path.abspath(path.dirname(__file__)))

    if args is None:
        args = argv[1:]

    r = [executable, "-m", "pytest", "-v"]
    r.extend(args)
    c = run(r).returncode
    if sysexit:
        return exit(c)
    else:
        return c

if __name__ == '__main__':
    main()