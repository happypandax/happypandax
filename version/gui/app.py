import sys
from PyQt5.QtCore import (Qt)
from PyQt5.QtGui import (QPixmap)
from PyQt5.QtWidgets import (QApplication, QMainWindow, QListView,
							 QHBoxLayout, QFrame, QWidget, QVBoxLayout,
							 QLabel)
from . import series

class AppWindow(QMainWindow):
	"The application's main window"
	def __init__(self):
		super().__init__()
		self.center = QWidget()
		self.setCentralWidget(self.center)
		self.leftDisplay()
		self.h_layout = QHBoxLayout()
		self.h_layout.addWidget(self.frame)
		
		self.manga_view = series.Display(self)
		self.chapter_view = QWidget()
		self.init_manga_view()

		self.center.setLayout(self.h_layout)
		self.setWindowTitle("Sadpanda")
		self.resize(980, 650)
		self.show()

	def leftDisplay(self):
		self.frame = QFrame()
		self.frame.setFrameShape(QFrame.StyledPanel)
		self.frame.setMinimumWidth(200)


	def init_manga_view(self):
		"initiates manga view"
		self.change_display("manga")
		self.manga_model = series.SeriesModel()
		self.manga_delegate = series.CustomDelegate()
		self.manga_view.setModel(self.manga_model)
		self.manga_view.setItemDelegate(self.manga_delegate)

		self.h_layout.addWidget(self.manga_view)

	def init_chapter_view(self):
		"Initiates chapter view"
		self.change_display("chapter")
		layout = QVBoxLayout()
		label = QLabel("Example Text")
		for x in range(20): layout.addWidget(label)
		self.chapter_view.setLayout(layout)
		
		self.h_layout.addWidget(self.chapter_view)


	def change_display(self, name):
		if name == "chapter":
			if not self.chapter_view.isVisible():
				self.manga_view.hide()
				self.chapter_view.show()
		elif name == "manga":
			if not self.manga_view.isVisible():
				self.chapter_view.hide()
				self.manga_view.show()

def run():
	"run from main"
	app = QApplication(sys.argv)
	window = AppWindow()
	sys.exit(app.exec_())

if __name__ == '__main__':
	raise NotImplementedError("Unit testing not implemented yet!")