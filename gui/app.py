import sys
from PyQt5.QtCore import (Qt)
from PyQt5.QtGui import (QPixmap)
from PyQt5.QtWidgets import (QApplication, QMainWindow, QListView)
import series

class AppWindow(QMainWindow):
	"The application's main window"
	def __init__(self):
		super().__init__()
		self.initUI()

	def initUI(self):
		"initiates UI"
		pass

class Display(QListView):
	"""TODO: Inherit from QListView, and add grid view functionalities
	hint: add resize funtionality extra: (zoom-in/zoom-out) mousekeys
	hint: add ability to move but snap to grid (QListView.Snap & setGridSize())
	TODO: REMEMBER TO ADD GRID BUTTONS TO BUTTONGROUP (check gui_constants)
	"""
	pass

if __name__ == '__main__':
	raise NotImplementedError("Unit testing not implemented yet!")