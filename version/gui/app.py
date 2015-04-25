import sys
from PyQt5.QtCore import (Qt)
from PyQt5.QtGui import (QPixmap)
from PyQt5.QtWidgets import (QApplication, QMainWindow, QListView,
							 QHBoxLayout)
from . import series

class AppWindow(QMainWindow):
	"The application's main window"
	def __init__(self):
		super().__init__()
		self.initUI()

	def initUI(self):
		"initiates UI"
		self.view = series.Display(self)
		self.model = series.SeriesModel()
		self.delegate = series.CustomDelegate()
		self.view.setModel(self.model)
		self.view.setItemDelegate(self.delegate)
		#h = QHBoxLayout()
		#h.addWidget(display)

		self.setCentralWidget(self.view)
		self.setWindowTitle("Sadpanda")
		self.resize(1200, 500)
		self.show()

def run():
	"run from main"
	app = QApplication(sys.argv)
	window = AppWindow()
	sys.exit(app.exec_())

if __name__ == '__main__':
	raise NotImplementedError("Unit testing not implemented yet!")