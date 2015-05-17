import time, datetime

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

def open(filepath):
	pass 
