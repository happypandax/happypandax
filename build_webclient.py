import os
import sass

from subprocess import run

def main():
	js_dir = "static"
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
	os.chdir(js_dir)

	run(["transcrypt", "-b", "-a", "-m", "-dt", "-da", "-de", "-dm", "-p", ".none", "-e", "6", "-n", ".\main.py"])

if __name__ == '__main__':
	main()