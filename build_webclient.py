import os
import shutil

from subprocess import run

def main():
    js_dir = "templates"
    js_out = "static/lib"
    js_files = "__javascript__"

    sass_file_input = "static/scss/_style.scss"
    sass_dir_input = "static/scss"
    sass_dir_output = "static/css"

    #print("Compiling SCSS... ", end="")
    #sass_string = sass.compile(filename=sass_file_input,
    #                           include_paths=[x.path for x in os.scandir(sass_dir_input) if x.is_dir])
    #if not os.path.isdir(sass_dir_output):
    #    os.makedirs(sass_dir_output)
    #with open(os.path.join(sass_dir_output,os.path.splitext(
    #    os.path.split(sass_file_input)[1])[0].replace("_", "", 1)+'.css')
    #          , "w+", encoding='utf-8') as f:
    #    f.write(sass_string)
    #print("complete")

    # Note: 
    # Transcrypt is required to be in the same directory as the js files
    o_cwd = os.getcwd()
    os.chdir(js_dir)
    run(["transcrypt", "-b", "-a", "-m", "-dt", "--dassert", "-de", "-dm", "-p", ".none", "-e", "6", "-n", ".\main.py"])
    os.chdir(o_cwd)

    root_js_files = os.path.join(js_dir, js_files)
    if os.path.exists(root_js_files):
        if os.path.exists(js_out):
            shutil.rmtree(js_out)
        os.makedirs(js_out)
        shutil.move(root_js_files, js_out)

    for src_dir, dirs, files in os.walk(js_dir):
        if js_files in dirs:
            out_dir = os.path.join(js_out, src_dir)
            if os.path.exists(out_dir):
                shutil.rmtree(out_dir)
            shutil.move(os.path.join(src_dir, js_files), os.path.join(out_dir, js_files))


if __name__ == '__main__':
    main()