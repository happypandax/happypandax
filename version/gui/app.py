import sys
from PyQt5.QtCore import (Qt, QSize, pyqtSignal)
from PyQt5.QtGui import (QPixmap, QIcon)
from PyQt5.QtWidgets import (QApplication, QMainWindow, QListView,
							 QHBoxLayout, QFrame, QWidget, QVBoxLayout,
							 QLabel, QStackedLayout, QToolBar, QMenuBar,
							 QSizePolicy, QMenu, QAction, QLineEdit,
							 QSplitter)
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
		self.resize(1098, 650)
		self.show()

	def manga_display(self):
		"initiates the manga view"
		self.manga_view = QSplitter()
		self.manga_view.setHandleWidth(3)
		manga_frame = QFrame()
		manga_frame.setFrameShape(QFrame.StyledPanel)
		manga_frame.setMaximumWidth(215)
		self.manga_model = series.SeriesModel()
		manga_delegate = series.CustomDelegate()
		manga_list_view = series.MangaView()
		manga_list_view.setModel(self.manga_model)
		manga_list_view.setItemDelegate(manga_delegate)
		self.manga_view.addWidget(manga_frame)
		self.manga_view.addWidget(manga_list_view)
		self.manga_view.setCollapsible(0, True)
		self.manga_view.setCollapsible(1, False)


	def chapter_display(self):
		"Initiates chapter view"
		self.chapter_view = QSplitter()
		self.chapter_view.setOrientation(Qt.Vertical)
		self.chapter_view.setHandleWidth(3)

		self.chapter_upper = series.ChapterUpper()
		self.chapter_view.addWidget(self.chapter_upper)

		chapter_list_view = series.ChapterView()
		self.chapter_view.addWidget(chapter_list_view)
		self.chapter_view.setCollapsible(0, True)
		self.chapter_view.setCollapsible(1, False)

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

		populate_action = QAction(chapter_view_icon, "Populate", self)
		populate_action.triggered.connect(lambda: self.manga_model.populate())
		self.toolbar.addAction(populate_action)

		spacer_middle = QWidget() # aligns buttons to the right
		spacer_middle.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
		self.toolbar.addWidget(spacer_middle)
		
		self.search_bar = QLineEdit()
		self.search_bar.setPlaceholderText("Search title, artist, genres")
		self.search_bar.setMaximumWidth(200)
		self.toolbar.addWidget(self.search_bar)
		self.toolbar.addAction("Search")
		self.toolbar.addAction("Ab&out")
		self.addToolBar(self.toolbar)
		
		spacer_end = QWidget() # aligns About action properly
		spacer_end.setFixedSize(QSize(10, 1))
		self.toolbar.addWidget(spacer_end)

	def setCurrentIndex(self, number, index=None):
		"""Changes the current display view.
		Params:
			number <- int (0 for manga view, 1 for chapter view
		Optional:
			index <- QModelIndex for chapter view
		Note: 0-based indexing
		"""
		if index is not None:
			self.chapter_upper.display_manga(index)
			self.display.setCurrentIndex(number)
		else:
			self.display.setCurrentIndex(number)

if __name__ == '__main__':
	raise NotImplementedError("Unit testing not implemented yet!")