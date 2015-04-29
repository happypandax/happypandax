import sys
from PyQt5.QtCore import (Qt, QSize, pyqtSignal)
from PyQt5.QtGui import (QPixmap, QIcon)
from PyQt5.QtWidgets import (QApplication, QMainWindow, QListView,
							 QHBoxLayout, QFrame, QWidget, QVBoxLayout,
							 QLabel, QStackedLayout, QToolBar, QMenuBar,
							 QSizePolicy, QMenu, QAction, QLineEdit)
from . import series

class AppWindow(QMainWindow):
	"The application's main window"
	def __init__(self):
		super().__init__()
		self.center = QWidget()
		self.display = QStackedLayout()
		self.center.setLayout(self.display)
		# init toolbar
		self.init_toolbar()
		# init the manga view variables
		self.manga_display()
		# init the chapter view variables
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
		manga_list_view = series.MangaView()
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
		chapter_upper = QFrame()
		chapter_upper.setMinimumHeight(200)
		chapter_upper.setFrameStyle(1)
		chapter_upper.setLineWidth(2)
		chapter_h = QHBoxLayout()
		self.label = QLabel("Example Text")
		for x in range(10):
			chapter_h.addWidget(self.label)
		chapter_upper.setLayout(chapter_h)
		chapter_layout.addWidget(chapter_upper)
		chapter_list_view = series.ChapterView()
		chapter_layout.addWidget(chapter_list_view)
		self.chapter_view = QFrame()
		self.chapter_view.setFrameStyle(QFrame.NoFrame)
		self.chapter_view.setLayout(chapter_layout)

	def init_toolbar(self):
		self.toolbar = QToolBar()
		self.toolbar.setFixedHeight(50)
		self.toolbar.setWindowTitle("Show") # text for the contextmenu
		#self.toolbar.setStyleSheet("QToolBar {border:0px}") # make it user defined?
		self.toolbar.setMovable(False)
		self.toolbar.setFloatable(False)
		self.toolbar.setIconSize(QSize(35,35))
		self.toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

		spacer_start = QWidget() # aligns the first actions properly
		spacer_start.setFixedSize(QSize(10, 1))
		self.toolbar.addWidget(spacer_start)

		from . import gui_constants
		manga_view_icon = QIcon(gui_constants.PIXMAP_PATH)
		manga_view_action = QAction(manga_view_icon, "Manga View", self)
		manga_view_action.setText("Manga View")
		manga_view_action.triggered.connect(lambda: self.setCurrentIndex(0)) #need lambda to pass extra args
		self.toolbar.addAction(manga_view_action)

		chapter_view_icon = QIcon(gui_constants.PIXMAP_PATH)
		chapter_view_action = QAction(chapter_view_icon, "Chapter View", self)
		chapter_view_action.setText("Chapter View")
		chapter_view_action.triggered.connect(lambda: self.setCurrentIndex(1)) #need lambda to pass extra args
		self.toolbar.addAction(chapter_view_action)

		spacer_middle = QWidget() # aligns buttons to the right
		spacer_middle.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
		self.toolbar.addWidget(spacer_middle)
		
		self.toolbar.addAction("Ab&out")
		self.addToolBar(self.toolbar)
		
		spacer_end = QWidget() # aligns About action properly
		spacer_end.setFixedSize(QSize(20, 1))
		self.toolbar.addWidget(spacer_end)

	def setCurrentIndex(self, number, data=None):
		"""Changes the current display view.
		Note: 0-based indexing
		"""
		if data is not None:
			self.label.setText(data[0])
			self.display.setCurrentIndex(number)
		else:
			self.display.setCurrentIndex(number) # shows the previous clicked manga

if __name__ == '__main__':
	raise NotImplementedError("Unit testing not implemented yet!")