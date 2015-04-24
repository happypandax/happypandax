import sys
from PyQt5.QtCore import (Qt, QSize)
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
		self.view = Display()
		self.model = series.SeriesModel(self.view)
		self.view.setModel(self.model)
		#h = QHBoxLayout()
		#h.addWidget(display)

		self.setCentralWidget(self.view)
		self.setWindowTitle("Sadpanda")
		self.resize(700,500)
		self.show()

class Display(QListView):
	"""TODO: Inherit from QListView, and add grid view functionalities
	hint: add resize funtionality extra: (zoom-in/zoom-out) mousekeys
	hint: add ability to move but snap to grid (QListView.Snap & setGridSize())
	"""
	def __init__(self):
		super().__init__()
		self.setAlternatingRowColors(True)
		self.setViewMode(self.IconMode)
		self.setSpacing(100)
		self.setGridSize(QSize(10,10))

def run():
	app = QApplication(sys.argv)
	window = AppWindow()
	sys.exit(app.exec_())

if __name__ == '__main__':
	raise NotImplementedError("Unit testing not implemented yet!")