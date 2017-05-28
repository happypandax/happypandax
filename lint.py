import os
import sys
from subprocess import run

def main():
    if not os.path.isdir("happypanda"):
        print("This file needs to be run in the same directory as the 'happypanda/' directory")
        sys.exit()

    for root, dirs, files in os.walk("happypanda"):

        for f in files:
            if f.endswith('.py'):
                f_path = os.path.join(root, f)
                print("Auto formatting", f_path)
                run(["autopep8", "--in-place", "-a", f_path])

    print("Running flake8...\n")
    return run(["flake8", "--config", "./setup.cfg", "happypanda"]).returncode

if __name__ == '__main__':
    sys.exit(main())