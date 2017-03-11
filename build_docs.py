import os
import shutil
from subprocess import run

run(["sphinx-build", "-b", "html", "docs/source", "docs/build"])

root_src_dir = "docs/build"
root_dst_dir = "docs/"

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