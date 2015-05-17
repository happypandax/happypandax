import time, datetime, os, subprocess, sys

IMG_FILES =  ['jpg','bmp','png','gif']

def today():
	"Returns current date in a list: [dd, Mmm, yyyy]"
	_date = datetime.date.today()
	day = _date.strftime("%d")
	month = _date.strftime("%b")
	year = _date.strftime("%Y")
	return [day, month, year]

def exception_handler(msg):
	"Spawns a dialog with the specified msg"
	pass

def open(chapterpath):

	filepath = os.path.join(chapterpath, [x for x in sorted(os.listdir(chapterpath))\
		if x[-3:] in IMG_FILES][0]) # Find first page

	if sys.platform.startswith('darwin'):
		subprocess.call(('open', filepath))
	elif os.name == 'nt':
		os.startfile(filepath)
	elif os.name == 'posix':
		subprocess.call(('xdg-open', filepath))
