import sys
from PyQt5.QtCore import (Qt, QSize, pyqtSignal, QThread, QEvent)
from PyQt5.QtGui import (QPixmap, QIcon, QMouseEvent)
from PyQt5.QtWidgets import (QApplication, QMainWindow, QListView,
							 QHBoxLayout, QFrame, QWidget, QVBoxLayout,
							 QLabel, QStackedLayout, QToolBar, QMenuBar,
							 QSizePolicy, QMenu, QAction, QLineEdit,
							 QSplitter)
from . import series
from . import gui_constants

class AppWindow(QMainWindow):
	"The application's main window"
	def __init__(self):
		super().__init__()
		self.center = QWidget()
		self.display = QStackedLayout()
		self.center.setLayout(self.display)
		# init the manga view variables
		self.manga_display()
		# init the chapter view variables
		self.chapter_display()
		# init toolbar
		self.init_toolbar()

		self.display.addWidget(self.manga_main)
		self.display.addWidget(self.chapter_main)

		self.setCentralWidget(self.center)
		self.setWindowTitle("Sadpanda")
		self.resize(1065, 650)
		self.show()

	def manga_display(self):
		"initiates the manga view"
		self.manga_main = QWidget()
		self.manga_view = QHBoxLayout()
		self.manga_main.setLayout(self.manga_view)

		manga_delegate = series.CustomDelegate()
		self.manga_list_view = series.MangaView()
		self.manga_list_view.setItemDelegate(manga_delegate)
		self.manga_view.addWidget(self.manga_list_view)

	def favourite_display(self):
		"initiates favourite display"
		pass

	def chapter_display(self):
		"Initiates chapter view"
		self.chapter_main = QWidget()
		self.chapter_layout = QHBoxLayout()
		self.chapter_main.setLayout(self.chapter_layout)

		#self.chapter_info.setContentsMargins(-8,-7,-7,-7)
		#self.chapter_info.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
		self.chapter_info_view = series.ChapterInfo()
		self.chapter_layout.addWidget(self.chapter_info_view)

		chapter_list_view = series.ChapterView()
		self.chapter_layout.addWidget(chapter_list_view)
		#self.chapter.setCollapsible(0, True)
		#self.chapter.setCollapsible(1, False)

	def init_toolbar(self):
		self.toolbar = QToolBar()
		self.toolbar.setFixedHeight(40)
		self.toolbar.setWindowTitle("Show") # text for the contextmenu
		#self.toolbar.setStyleSheet("QToolBar {border:0px}") # make it user defined?
		self.toolbar.setMovable(False)
		self.toolbar.setFloatable(False)
		self.toolbar.setIconSize(QSize(35,35))
		self.toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

		spacer_start = QWidget() # aligns the first actions properly
		spacer_start.setFixedSize(QSize(10, 1))
		self.toolbar.addWidget(spacer_start)

		favourite_view_icon = QIcon(gui_constants.STAR_BTN_PATH)
		favourite_view_action = QAction(favourite_view_icon, "Favourite", self)
		#favourite_view_action.setText("Manga View")
		favourite_view_action.triggered.connect(lambda: self.setCurrentIndex(1)) #need lambda to pass extra args
		self.toolbar.addAction(favourite_view_action)

		catalog_view_icon = QIcon(gui_constants.HOME_BTN_PATH)
		catalog_view_action = QAction(catalog_view_icon, "Catalog", self)
		#catalog_view_action.setText("Catalog")
		catalog_view_action.triggered.connect(lambda: self.setCurrentIndex(0)) #need lambda to pass extra args
		self.toolbar.addAction(catalog_view_action)
		self.toolbar.addSeparator()

		series_icon = QIcon(gui_constants.PLUS_PATH)
		series_action = QAction(series_icon, "Add series...", self)
		series_action.triggered.connect(self.manga_list_view.SERIES_DIALOG.emit)
		series_menu = QMenu()
		series_menu.addSeparator()
		populate_action = QAction("Populate from folder...", self)
		populate_action.triggered.connect(lambda:series.populate())
		series_menu.addAction(populate_action)
		series_action.setMenu(series_menu)
		self.toolbar.addAction(series_action)

		spacer_middle = QWidget() # aligns buttons to the right
		spacer_middle.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
		self.toolbar.addWidget(spacer_middle)
		
		self.search_bar = QLineEdit()
		self.search_bar.setPlaceholderText("Search title, artist, genres")
		self.search_bar.setMaximumWidth(200)
		self.toolbar.addWidget(self.search_bar)
		self.toolbar.addSeparator()
		settings_icon = QIcon(gui_constants.SETTINGS_PATH)
		settings_action = QAction(settings_icon, "Set&tings", self)
		self.toolbar.addAction(settings_action)
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
			self.chapter_info_view.display_manga(index)
			self.display.setCurrentIndex(number)
		else:
			self.display.setCurrentIndex(number)

if __name__ == '__main__':
	raise NotImplementedError("Unit testing not implemented yet!")