#NOTE: import like this:
# version.parent.childs
from PyQt5.QtWidgets import QApplication
from sys import argv, exit

if __name__ == '__main__':
	app = QApplication(argv)
	from version.constants import WINDOW
	exit(app.exec_())
