import sys
from PyQt5.QtCore import (Qt)
from PyQt5.QtGui import (QPixmap)
from PyQt5.QtWidgets import (QApplication, QMainWindow, QListView,
							 QHBoxLayout, QFrame, QWidget, QVBoxLayout,
							 QLabel, QStackedLayout)
from . import series

class AppWindow(QMainWindow):
	"The application's main window"
	def __init__(self):
		super().__init__()
		self.center = QWidget()
		self.display = QStackedLayout()
		self.center.setLayout(self.display)
		self.manga_display()
		self.chapter_display()
		
		self.display.addWidget(self.manga_view)
		self.display.addWidget(self.chapter_view)

		self.setCentralWidget(self.center)
		self.setWindowTitle("Sadpanda")
		self.resize(980, 650)
		self.show()

	def manga_display(self):
		"initiates the manga view"
		manga_frame = QFrame()
		manga_frame.setFrameShape(QFrame.StyledPanel)
		manga_frame.setMinimumWidth(200)
		manga_model = series.SeriesModel()
		manga_delegate = series.CustomDelegate()
		manga_list_view = series.Display()
		manga_list_view.setModel(manga_model)
		manga_list_view.setItemDelegate(manga_delegate)
		manga_layout = QHBoxLayout()
		manga_layout.addWidget(manga_frame)
		manga_layout.addWidget(manga_list_view)
		self.manga_view = QFrame()
		self.manga_view.setFrameShape(QFrame.NoFrame)
		self.manga_view.setLayout(manga_layout)


	def chapter_display(self):
		"Initiates chapter view"
		chapter_layout = QVBoxLayout()
		label = QLabel("Example Text")
		for x in range(20): chapter_layout.addWidget(label)
		self.chapter_view = QFrame()
		self.chapter_view.setFrameStyle(QFrame.NoFrame)
		self.chapter_view.setLayout(chapter_layout)

	def setCurrentIndex(self, number):
		"""Changes the current display view.
		Note: 0-based indexing
		"""
		self.display.setCurrentIndex(number)


if __name__ == '__main__':
	raise NotImplementedError("Unit testing not implemented yet!")