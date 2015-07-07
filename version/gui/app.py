"""
This file is part of Happypanda.
Happypanda is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
any later version.
Happypanda is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with Happypanda.  If not, see <http://www.gnu.org/licenses/>.
"""

import sys, logging, os, threading, re, pickle, requests
from PyQt5.QtCore import (Qt, QSize, pyqtSignal, QThread, QEvent, QTimer,
						  QObject)
from PyQt5.QtGui import (QPixmap, QIcon, QMouseEvent, QCursor)
from PyQt5.QtWidgets import (QApplication, QMainWindow, QListView,
							 QHBoxLayout, QFrame, QWidget, QVBoxLayout,
							 QLabel, QStackedLayout, QToolBar, QMenuBar,
							 QSizePolicy, QMenu, QAction, QLineEdit,
							 QSplitter, QMessageBox, QFileDialog,
							 QDesktopWidget, QPushButton, QCompleter,
							 QListWidget, QListWidgetItem, QToolTip)
from . import (gui_constants, misc, gallery, file_misc, settingsdialog,
			   gallerydialog)
from ..database import fetch, gallerydb
from .. import settings, pewnet

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical

class AppWindow(QMainWindow):
	"The application's main window"
	def __init__(self):
		super().__init__()
		self.first_time()
		self.initUI()
		self.init_watchers()

	def init_watchers(self):

		def find_index(gallery_id):
			index = None
			rows = self.manga_list_view.gallery_model.rowCount()
			for r in range(rows):
				indx = self.manga_list_view.gallery_model.index(r, 1)
				m_gallery = indx.data(Qt.UserRole+1)
				if m_gallery.id == gallery_id:
					index = indx
					break
			return index

		def remove_gallery(g):
			index = find_index(g.id)
			if index:
				self.manga_list_view.remove_gallery([index])

		def create_gallery(path):
			g_dia = gallerydialog.GalleryDialog(self, path)
			g_dia.SERIES.connect(self.manga_list_view.gallery_model.addRows)
			g_dia.show()

		def update_gallery(g):
			index = find_index(g.id)
			if index:
				self.manga_list_view.replace_edit_gallery([g], index.row())
			else:
				log_e('Could not find gallery to update from Watcher')

		def created(path):
			c_popup = file_misc.CreatedPopup(path, self)
			c_popup.ADD_SIGNAL.connect(create_gallery)
		def modified(path, gallery):
			mod_popup = file_misc.ModifiedPopup(path, gallery, self)
		def deleted(path, gallery):
			d_popup = file_misc.DeletedPopup(path, gallery, self)
			d_popup.UPDATE_SIGNAL.connect(update_gallery)
			d_popup.REMOVE_SIGNAL.connect(remove_gallery)
		def moved(new_path, gallery):
			mov_popup = file_misc.MovedPopup(new_path, gallery, self)
			mov_popup.UPDATE_SIGNAL.connect(update_gallery)

		self.watchers = file_misc.Watchers()
		self.watchers.gallery_handler.CREATE_SIGNAL.connect(created)
		self.watchers.gallery_handler.MODIFIED_SIGNAL.connect(modified)
		self.watchers.gallery_handler.MOVED_SIGNAL.connect(moved)
		self.watchers.gallery_handler.DELETED_SIGNAL.connect(deleted)

	def initUI(self):
		self.center = QWidget()
		self.display = QStackedLayout()
		self.center.setLayout(self.display)
		# init the manga view variables
		self.manga_display()
		log_d('Create manga display: OK')
		# init the chapter view variables
		#self.chapter_display()
		# init toolbar
		self.init_toolbar()
		log_d('Create toolbar: OK')
		# init status bar
		self.init_stat_bar()
		log_d('Create statusbar: OK')

		self.m_l_view_index = self.display.addWidget(self.manga_list_main)
		self.m_t_view_index = self.display.addWidget(self.manga_table_view)
		#self.display.addWidget(self.chapter_main)

		self.setCentralWidget(self.center)
		self.setWindowTitle("Happypanda")
		self.setWindowIcon(QIcon(gui_constants.APP_ICO_PATH))
		props = settings.win_read(self, 'AppWindow')
		if props.resize:
			x, y = props.resize
			self.resize(x, y)
		else:
			self.resize(gui_constants.MAIN_W, gui_constants.MAIN_H)
		posx, posy = props.pos
		self.move(posx, posy)
		self.show()
		log_d('Show window: OK')

		class upd_chk(QObject):
			UPDATE_CHECK = pyqtSignal(str)
			def __init__(self, **kwargs):
				super().__init__(**kwargs)
			def fetch_vs(self):
				import requests
				import time
				try:
					log_d('Checking Update')
					time.sleep(1.5)
					r = requests.get("https://raw.githubusercontent.com/Pewpews/happypanda/master/VS.txt")
					a = r.text
					vs = a.strip()
					self.UPDATE_CHECK.emit(vs)
				except:
					log_d('Checking Update: FAIL')
					pass

		update_instance = upd_chk()
		thread = QThread()
		update_instance.moveToThread(thread)
		update_instance.UPDATE_CHECK.connect(self.check_update)
		thread.started.connect(update_instance.fetch_vs)
		update_instance.UPDATE_CHECK.connect(lambda: update_instance.deleteLater)
		update_instance.UPDATE_CHECK.connect(lambda: thread.deleteLater)
		thread.start()
		log_d('Window Create: OK')
		#QTimer.singleShot(3000, self.check_update)

	def check_update(self, vs):
		try:
			if vs != gui_constants.vs:
				msgbox = QMessageBox()
				msgbox.setText("Update {} is available!".format(vs))
				msgbox.setDetailedText(
"""How to update:
1. Get the newest release from:
https://github.com/Pewpews/happypanda/releases

2. Overwrite your files with the new files.

Your database will not be touched without you being notified.""")
				msgbox.setStandardButtons(QMessageBox.Ok)
				msgbox.setDefaultButton(QMessageBox.Ok)
				msgbox.setWindowIcon(QIcon(gui_constants.APP_ICO_PATH))
				msgbox.exec()
		except:
			pass

	#def style_tooltip(self):
	#	palette = QToolTip.palette()
	#	palette.setColor()

	def init_stat_bar(self):
		self.status_bar = self.statusBar()
		self.status_bar.setMaximumHeight(20)
		self.status_bar.setSizeGripEnabled(False)
		self.stat_info = QLabel()
		self.stat_info.setIndent(5)
		self.sort_main = QAction("Asc", self)
		sort_menu = QMenu()
		self.sort_main.setMenu(sort_menu)
		s_by_title = QAction("Title", sort_menu)
		s_by_artist = QAction("Artist", sort_menu)
		sort_menu.addAction(s_by_title)
		sort_menu.addAction(s_by_artist)
		self.status_bar.addPermanentWidget(self.stat_info)
		#self.status_bar.addAction(self.sort_main)
		self.temp_msg = QLabel()
		self.temp_timer = QTimer()

		self.manga_list_view.gallery_model.ROWCOUNT_CHANGE.connect(self.stat_row_info)
		self.manga_list_view.gallery_model.STATUSBAR_MSG.connect(self.stat_temp_msg)
		self.manga_list_view.STATUS_BAR_MSG.connect(self.stat_temp_msg)
		self.manga_table_view.STATUS_BAR_MSG.connect(self.stat_temp_msg)
		self.stat_row_info()

	def stat_temp_msg(self, msg):
		self.temp_timer.stop()
		self.temp_msg.setText(msg)
		self.status_bar.addWidget(self.temp_msg)
		self.temp_timer.timeout.connect(self.temp_msg.clear)
		self.temp_timer.setSingleShot(True)
		self.temp_timer.start(5000)

	def stat_row_info(self):
		r = self.manga_list_view.model().rowCount()
		t = len(self.manga_list_view.gallery_model._data)
		self.stat_info.setText("Loaded {} of {} ".format(r, t))

	def manga_display(self):
		"initiates the manga view"
		#list view
		self.manga_list_main = QWidget()
		#self.manga_list_main.setContentsMargins(-10, -12, -10, -10)
		self.manga_list_main.setContentsMargins(10, -9, -10, -10) # x, y, inverted_width, inverted_height
		self.manga_list_layout = QHBoxLayout()
		self.manga_list_main.setLayout(self.manga_list_layout)

		self.manga_list_view = gallery.MangaView(self)
		self.manga_list_view.clicked.connect(self.popup)
		self.manga_list_view.manga_delegate.POPUP.connect(self.popup)
		self.popup_window = self.manga_list_view.manga_delegate.popup_window
		self.manga_list_layout.addWidget(self.manga_list_view)

		#table view
		self.manga_table_main = QWidget()
		self.manga_table_layout = QVBoxLayout()
		self.manga_table_main.setLayout(self.manga_table_layout)

		self.manga_table_view = gallery.MangaTableView(self)
		self.manga_table_view.gallery_model = self.manga_list_view.gallery_model
		self.manga_table_view.sort_model = self.manga_list_view.sort_model
		self.manga_table_view.setModel(self.manga_table_view.sort_model)
		self.manga_table_view.sort_model.change_model(self.manga_table_view.gallery_model)
		self.manga_table_view.setColumnWidth(gui_constants.FAV, 20)
		self.manga_table_view.setColumnWidth(gui_constants.ARTIST, 200)
		self.manga_table_view.setColumnWidth(gui_constants.TITLE, 400)
		self.manga_table_view.setColumnWidth(gui_constants.TAGS, 300)
		self.manga_table_view.setColumnWidth(gui_constants.TYPE, 60)
		self.manga_table_view.setColumnWidth(gui_constants.CHAPTERS, 60)
		self.manga_table_view.setColumnWidth(gui_constants.LANGUAGE, 100)
		self.manga_table_view.setColumnWidth(gui_constants.LINK, 400)
		self.manga_table_layout.addWidget(self.manga_table_view)


	def search(self, srch_string):
		case_ins = srch_string.lower()
		if not gui_constants.ALLOW_SEARCH_REGEX:
			remove = '^$*+?{}\\|()[]'
			for x in remove:
				if x == '[' or x == ']':
					continue
				else:
					case_ins = case_ins.replace(x, '.')
		else:
			try:
				re.compile(case_ins)
			except re.error:
				return
		self.manga_list_view.sort_model.search(case_ins)

	def popup(self, index):
		if not self.popup_window.isVisible():
			m_x = QCursor.pos().x()
			m_y = QCursor.pos().y()
			d_w = QDesktopWidget().width()
			d_h = QDesktopWidget().height()
			p_w = gui_constants.POPUP_WIDTH
			p_h = gui_constants.POPUP_HEIGHT
			
			index_rect = self.manga_list_view.visualRect(index)
			index_point = self.manga_list_view.mapToGlobal(index_rect.topRight())
			# adjust so it doesn't go offscreen
			if d_w - m_x < p_w and d_h - m_y < p_h: # bottom
				self.popup_window.move(m_x-p_w+5, m_y-p_h)
			elif d_w - m_x > p_w and d_h - m_y < p_h:
				self.popup_window.move(m_x+5, m_y-p_h)
			elif d_w - m_x < p_w:
				self.popup_window.move(m_x-p_w+5, m_y+5)
			else:
				self.popup_window.move(index_point)

			self.popup_window.set_gallery(index.data(Qt.UserRole+1))
			self.popup_window.show()

	def favourite_display(self):
		"Switches to favourite display"
		if self.display.currentIndex() == self.m_l_view_index:
			self.manga_list_view.sort_model.fav_view()
		else:
			self.manga_table_view.sort_model.fav_view()

	def catalog_display(self):
		"Switches to catalog display"
		if self.display.currentIndex() == self.m_l_view_index:
			self.manga_list_view.sort_model.catalog_view()
		else:
			self.manga_table_view.sort_model.catalog_view()

	def settings(self):
		#about = misc.About()
		sett = settingsdialog.SettingsDialog(self)
		sett.scroll_speed_changed.connect(self.manga_list_view.updateGeometries)
		#sett.show()

	def init_toolbar(self):
		self.toolbar = QToolBar()
		self.toolbar.setFixedHeight(30)
		self.toolbar.setWindowTitle("Show") # text for the contextmenu
		#self.toolbar.setStyleSheet("QToolBar {border:0px}") # make it user defined?
		self.toolbar.setMovable(False)
		self.toolbar.setFloatable(False)
		#self.toolbar.setIconSize(QSize(20,20))
		self.toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)

		spacer_start = QWidget() # aligns the first actions properly
		spacer_start.setFixedSize(QSize(10, 1))
		self.toolbar.addWidget(spacer_start)

		favourite_view_icon = QIcon(gui_constants.STAR_BTN_PATH)
		favourite_view_action = QAction(favourite_view_icon, "Favorites", self)
		favourite_view_action.setToolTip('Show only favourite galleries')
		favourite_view_action.triggered.connect(self.favourite_display) #need lambda to pass extra args
		self.toolbar.addAction(favourite_view_action)

		catalog_view_icon = QIcon(gui_constants.HOME_BTN_PATH)
		catalog_view_action = QAction(catalog_view_icon, "Library", self)
		catalog_view_action.setToolTip('Show all your galleries')
		#catalog_view_action.setText("Catalog")
		catalog_view_action.triggered.connect(self.catalog_display) #need lambda to pass extra args
		self.toolbar.addAction(catalog_view_action)
		self.toolbar.addSeparator()

		gallery_icon = QIcon(gui_constants.PLUS_PATH)
		gallery_action = QAction(gallery_icon, "Add gallery", self)
		gallery_action.triggered.connect(self.manga_list_view.SERIES_DIALOG.emit)
		gallery_action.setToolTip('Add a single gallery thoroughly')
		gallery_menu = QMenu()
		gallery_menu.addSeparator()
		add_more_action = QAction("Add galleries...", self)
		add_more_action.setStatusTip('Add galleries from different folders')
		add_more_action.triggered.connect(lambda: self.populate(True))
		gallery_menu.addAction(add_more_action)
		populate_action = QAction("Populate from folder...", self)
		populate_action.setStatusTip('Populates the DB with galleries from a single folder')
		populate_action.triggered.connect(self.populate)
		gallery_menu.addAction(populate_action)
		gallery_action.setMenu(gallery_menu)
		self.toolbar.addAction(gallery_action)

		spacer_middle = QWidget() # aligns buttons to the right
		spacer_middle.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
		self.toolbar.addWidget(spacer_middle)
		
		self.grid_toggle_g_icon = QIcon(gui_constants.GRID_PATH)
		self.grid_toggle_l_icon = QIcon(gui_constants.LIST_PATH)
		self.grid_toggle = QAction(self.toolbar)
		self.grid_toggle.setObjectName('gridtoggle')
		self.grid_toggle.setIcon(self.grid_toggle_l_icon)
		self.grid_toggle.triggered.connect(self.toggle_view)
		self.toolbar.addAction(self.grid_toggle)

		self.search_bar = misc.LineEdit()
		if gui_constants.SEARCH_AUTOCOMPLETE:
			completer = QCompleter(self)
			completer.setModel(self.manga_list_view.gallery_model)
			completer.setCaseSensitivity(Qt.CaseInsensitive)
			completer.setCompletionMode(QCompleter.PopupCompletion)
			completer.setCompletionRole(Qt.DisplayRole)
			completer.setCompletionColumn(gui_constants.TITLE)
			completer.setFilterMode(Qt.MatchContains)
			self.search_bar.setCompleter(completer)
		if gui_constants.SEARCH_ON_ENTER:
			self.search_bar.returnPressed.connect(lambda: self.search(self.search_bar.text()))
		else:
			self.search_bar.textChanged[str].connect(self.search)
		self.search_bar.setPlaceholderText("Search guide located at About -> Search Guide")
		self.search_bar.setMinimumWidth(150)
		self.search_bar.setMaximumWidth(500)
		self.toolbar.addWidget(self.search_bar)
		self.toolbar.addSeparator()
		settings_icon = QIcon(gui_constants.SETTINGS_PATH)
		settings_action = QAction(settings_icon, "Set&tings", self)
		settings_action.triggered.connect(self.settings)
		self.toolbar.addAction(settings_action)
		
		spacer_end = QWidget() # aligns About action properly
		spacer_end.setFixedSize(QSize(10, 1))
		self.toolbar.addWidget(spacer_end)
		self.addToolBar(self.toolbar)

	def toggle_view(self):
		"""
		Toggles the current display view
		"""
		if self.display.currentIndex() == self.m_l_view_index:
			self.display.setCurrentIndex(self.m_t_view_index)
			self.grid_toggle.setIcon(self.grid_toggle_g_icon)
		else:
			self.display.setCurrentIndex(self.m_l_view_index)
			self.grid_toggle.setIcon(self.grid_toggle_l_icon)

	# TODO: Improve this so that it adds to the gallery dialog,
	# so user can edit data before inserting (make it a choice)
	def populate(self, mixed=None):
		"Populates the database with gallery from local drive'"
		if mixed:
			gallery_view = misc.GalleryListView(self, True)
			gallery_view.SERIES.connect(self.gallery_populate)
			gallery_view.show()
		else:
			path = QFileDialog.getExistingDirectory(None, "Choose a folder containing your galleries")
			self.gallery_populate(path, True)

	def gallery_populate(self, path, validate=False):
		"Scans the given path for gallery to add into the DB"
		if len(path) is not 0:
			data_thread = QThread()
			#loading_thread = QThread()
			loading = misc.Loading(self)
			if not loading.ON:
				misc.Loading.ON = True
				fetch_instance = fetch.Fetch()
				fetch_instance.series_path = path
				loading.show()

				def finished(status):
					def hide_loading():
						loading.hide()
					if status:
						if len(status) != 0:
							def add_gallery(gallery_list):
								class A(QObject):
									done = pyqtSignal()
									prog = pyqtSignal(int)
									def __init__(self, obj, parent=None):
										super().__init__(parent)
										self.obj = obj

									def add_to_db(self):
										p = 0
										for x in self.obj:
											gallerydb.GalleryDB.add_gallery(x)
											p += 1
											self.prog.emit(p)
										self.done.emit()

								loading.progress.setMaximum(len(gallery_list))
								a_instance = A(gallery_list)
								thread = QThread()
								def loading_show():
									loading.setText('Populating database.\nPlease wait...')
									loading.show()

								def loading_hide():
									loading.close()
									self.manga_list_view.gallery_model.populate_data()
									self.manga_list_view.refresh()
									self.manga_list_view.gallery_model.ROWCOUNT_CHANGE.emit()

								def del_later():
									try:
										a_instance.deleteLater()
										thread.deleteLater()
									except NameError:
										pass

								a_instance.moveToThread(thread)
								a_instance.prog.connect(loading.progress.setValue)
								thread.started.connect(loading_show)
								thread.started.connect(a_instance.add_to_db)
								a_instance.done.connect(loading_hide)
								a_instance.done.connect(del_later)
								thread.start()

							data_thread.quit
							hide_loading()
							log_i('Populating DB from gallery folder: OK')
							if validate:
								gallery_list = misc.GalleryListView(self)
								gallery_list.SERIES.connect(add_gallery)
								for ser in status:
									gallery_list.add_gallery(ser, os.path.split(ser.path)[1])
								#self.manga_list_view.gallery_model.populate_data()
								gallery_list.show()
							else:
								add_gallery(status)
							misc.Loading.ON = False
						else:
							log_d('No new gallery was found')
							loading.setText("No new gallery found")
							data_thread.quit
							misc.Loading.ON = False

					else:
						log_e('Populating DB from gallery folder: FAIL')
						loading.setText("<font color=red>An error occured. Check happypanda_log..</font>")
						loading.progress.setStyleSheet("background-color:red;")
						data_thread.quit
						QTimer.singleShot(5000, loading.close)

				def fetch_deleteLater():
					try:
						fetch_instance.deleteLater
					except NameError:
						pass

				def thread_deleteLater(): #NOTE: Isn't this bad?
					data_thread.deleteLater
					data_thread.quit()

				def a_progress(prog):
					loading.progress.setValue(prog)
					loading.setText("Searching for galleries...")

				fetch_instance.moveToThread(data_thread)
				fetch_instance.DATA_COUNT.connect(loading.progress.setMaximum)
				fetch_instance.PROGRESS.connect(a_progress)
				data_thread.started.connect(fetch_instance.local)
				fetch_instance.FINISHED.connect(finished)
				fetch_instance.FINISHED.connect(fetch_deleteLater)
				fetch_instance.FINISHED.connect(thread_deleteLater)
				data_thread.start()
				log_i('Populating DB from gallery folder')

	def first_time(self):
		if gui_constants.FIRST_TIME_LEVEL < 1:
			log_d('Invoking first time level 0')
			if gallerydb.GalleryDB.rebuild_galleries():
				settings.set(1, 'Application', 'first time level')

	def closeEvent(self, event):
		# watchers
		self.watchers.stop_all()

		# settings
		settings.win_save(self, 'AppWindow')

		# web session
		with open(gui_constants.SESSION_COOKIES_PATH, 'wb') as f:
			pickle.dump(requests.utils.dict_from_cookiejar(pewnet.web_session.cookies), f)
		
		# temp dir
		try:
			for root, dirs, files in os.walk('temp', topdown=False):
				for name in files:
					os.remove(os.path.join(root, name))
				for name in dirs:
					os.rmdir(os.path.join(root, name))
			log_d('Empty temp on exit: OK')
		except:
			log_d('Empty temp on exit: FAIL')

		# error
		err = sys.exc_info()
		if all(err):
			log_c('Last error before exit:\n{}\n{}\n{}'.format(err[0], err[1], err[2]))
		else:
			log_d('Normal Exit App: OK')
		super().closeEvent(event)
		app = QApplication.instance()
		app.quit()
		sys.exit()

if __name__ == '__main__':
	raise NotImplementedError("Unit testing not implemented yet!")