import os
from subprocess import run


def main():
    js_dir = "templates"

    # Note:
    # Transcrypt is required to be in the same directory as the js files
    o_cwd = os.getcwd()
    os.chdir(js_dir)
    run(["transcrypt", "-b", "-n", "-a", "-m", "-dt", "--dassert", "-de", "-dm", "-p", ".none", "-e", "6", ".\main.py"])
    os.chdir(o_cwd)

if __name__ == '__main__':
    main()
