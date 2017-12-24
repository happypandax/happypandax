import os
import argparse
import sys
from subprocess import run


def main(args=sys.argv):
    js_dir = "templates"
    # Note:
    # Transcrypt is required to be in the same directory as the js files
    o_cwd = os.getcwd()
    os.chdir(js_dir)
    parser = argparse.ArgumentParser()
    parser.add_argument('-p', '--prod', help="Build a production version", action='store_true')
    args = parser.parse_args(args)
    if args.prod:
        print("======PRODUCTION BUILD=====")
        run(["transcrypt", "-b", "-n", "-p", ".none", ".\main.py"])
    else:
        print("======DEVELOPMENT BUILD====")
        run(["transcrypt", "-b", "-n", "-a", "-m", "-dt", "--dassert", "-de", "-dm", "-p", ".none", "-e", "6", ".\main.py"])
    os.chdir(o_cwd)


if __name__ == '__main__':
    main()
