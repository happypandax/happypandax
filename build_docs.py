import os
import shutil
import sys
from subprocess import run


def main():
    root_src_dir = "docs/build"
    root_dst_dir = "docs/"

    sphinx_path = "sphinx-build"

    if os.environ.get('APPVEYOR'):
        sphinx_path = os.path.join(os.path.split(sys.executable)[0], "Scripts", "sphinx-build.exe")

    run([sphinx_path, "-b", "html", "docs/source", root_src_dir])

    for src_dir, dirs, files in os.walk(root_src_dir):
        dst_dir = src_dir.replace(root_src_dir, root_dst_dir, 1)
        if not os.path.exists(dst_dir):
            os.makedirs(dst_dir)
        for file_ in files:
            src_file = os.path.join(src_dir, file_)
            dst_file = os.path.join(dst_dir, file_)
            if os.path.exists(dst_file):
                os.remove(dst_file)
            shutil.move(src_file, dst_dir)

    shutil.rmtree(root_src_dir)


if __name__ == '__main__':
    main()
