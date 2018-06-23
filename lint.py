import os
import sys
import argparse
from subprocess import run


def aformat(f_path):
    print("Auto formatting", f_path)
    run(["autopep8", "--in-place", "-a", "--max-line-length=120",
         "--ignore", "E24,W503,E711", f_path])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-f', '--format', action='store_true', help="Autoformat before running flake8")
    parser.add_argument('--cfg', help="Path to custom flake8 config", default="./setup.cfg")
    args = parser.parse_args()

    if not os.path.isdir("happypanda"):
        print("This file needs to be run in the same directory as the 'happypanda/' directory")
        sys.exit()

    if args.format:
        for p in ("happypanda", "templates"):
            for root, dirs, files in os.walk(p):

                for f in files:
                    if f.endswith('.py'):
                        f_path = os.path.join(root, f)
                        aformat(f_path)

        for d in (".", "migrate", "scripts"):
            for p in os.scandir(d):
                if p.name.endswith(".py"):
                    aformat(p.path)

    print("Running flake8...\n")
    flake8_path = "flake8"
    if os.environ.get('APPVEYOR'):
        flake8_path = os.path.join(os.path.split(sys.executable)[0], "Scripts", "flake8.exe")
    return run([flake8_path, "--config", args.cfg, "."]).returncode


if __name__ == '__main__':
    sys.exit(main())
