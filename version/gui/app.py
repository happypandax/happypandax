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

import sys, logging, os, threading, re, requests
from PyQt5.QtCore import (Qt, QSize, pyqtSignal, QThread, QEvent, QTimer,
						  QObject)
from PyQt5.QtGui import (QPixmap, QIcon, QMouseEvent, QCursor)
from PyQt5.QtWidgets import (QApplication, QMainWindow, QListView,
							 QHBoxLayout, QFrame, QWidget, QVBoxLayout,
							 QLabel, QStackedLayout, QToolBar, QMenuBar,
							 QSizePolicy, QMenu, QAction, QLineEdit,
							 QSplitter, QMessageBox, QFileDialog,
							 QDesktopWidget, QPushButton, QCompleter,
							 QListWidget, QListWidgetItem, QToolTip,
							 QProgressBar, QToolButton, QSystemTrayIcon)
from . import (gui_constants, misc, gallery, file_misc, settingsdialog,
			   gallerydialog)
from ..database import fetch, gallerydb
from .. import settings, pewnet, utils

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
		self.initUI()
		self.start_up()
		QTimer.singleShot(3000, self._check_update)

	def init_watchers(self):

		def remove_gallery(g):
			index = self.manga_list_view.find_index(g.id)
			if index:
				self.manga_list_view.remove_gallery([index])

		def create_gallery(path):
			g_dia = gallerydialog.GalleryDialog(self, path)
			g_dia.SERIES.connect(self.manga_list_view.gallery_model.addRows)
			g_dia.show()

		def update_gallery(g):
			index = self.manga_list_view.find_index(g.id)
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

		if gui_constants.LOOK_NEW_GALLERY_STARTUP:
			self.notification_bar.add_text("Looking for new galleries...")
			try:
				class ScanDir(QObject):
					final_paths_and_galleries = pyqtSignal(list, list)
					def __init__(self, model_data, parent=None):
						super().__init__(parent)
						self.model_data = model_data
					def scan_dirs(self):
						db_data = self.model_data
						paths = []
						for g in range(len(db_data)):
							paths.append(os.path.normcase(db_data[g].path))

						contents = []
						case_path = [] # needed for tile and artist parsing... e.g to avoid lowercase
						for m_path in gui_constants.MONITOR_PATHS:
							for p in os.listdir(m_path):
								abs_p = os.path.join(m_path, p)
								if os.path.isdir(abs_p) or \
									p.endswith(utils.ARCHIVE_FILES):
									case_path.append(abs_p)
									contents.append(os.path.normcase(abs_p))

						paths = sorted(paths)
						new_galleries = []
						for c, x in enumerate(contents):
							y = utils.b_search(paths, x)
							if not y:
								# (path, number for case_path)
								new_galleries.append((x, c))

						galleries = []
						final_paths = []
						if new_galleries:
							for g in new_galleries:
								gallery = gallerydb.Gallery()
								try:
									gallery.profile = utils.get_gallery_img(g[0])
								except:
									gallery.profile = gui_constants.NO_IMAGE_PATH
								parser_dict = utils.title_parser(os.path.split(case_path[g[1]])[1])
								gallery.title = parser_dict['title']
								gallery.artist = parser_dict['artist']
								galleries.append(gallery)
								final_paths.append(case_path[g[1]])
						self.final_paths_and_galleries.emit(final_paths, galleries)
					#if gui_constants.LOOK_NEW_GALLERY_AUTOADD:
					#	QTimer.singleShot(10000, self.gallery_populate(final_paths))
					#	return

				def show_new_galleries(final_paths, galleries):
					if final_paths and galleries:
						if gui_constants.LOOK_NEW_GALLERY_AUTOADD:
							self.gallery_populate(final_paths)
						else:
							if len(galleries) == 1:
								self.notification_bar.add_text("{} new gallery was discovered in one of your monitored directories".format(len(galleries)))
							else:
								self.notification_bar.add_text("{} new galleries were discovered in one of your monitored directories".format(len(galleries)))
							text = "These new galleries were discovered! Do you want to add them?"\
								if len(galleries) > 1 else "This new gallery was discovered! Do you want to add it?"
							g_popup = file_misc.GalleryPopup((text, galleries), self)
							buttons = g_popup.add_buttons('Add', 'Close')

							def populate_n_close():
								self.gallery_populate(final_paths)
								g_popup.close()
							buttons[0].clicked.connect(populate_n_close)
							buttons[1].clicked.connect(g_popup.close)

				thread = QThread(self)
				self.scan_inst = ScanDir(self.manga_list_view.gallery_model._data)
				self.scan_inst.moveToThread(thread)
				self.scan_inst.final_paths_and_galleries.connect(show_new_galleries)
				self.scan_inst.final_paths_and_galleries.connect(lambda a: self.scan_inst.deleteLater())
				thread.started.connect(self.scan_inst.scan_dirs)
				thread.finished.connect(thread.deleteLater)
				thread.start()
			except:
				self.notification_bar.add_text('An error occured while attempting to scan for new galleries. Check happypanda.log.')
				log.exception('An error occured while attempting to scan for new galleries.')

	def start_up(self):
		def normalize_first_time():
			settings.set(2, 'Application', 'first time level')
		def done():
			self.manga_list_view.gallery_model.init_data()
			if gui_constants.ENABLE_MONITOR and\
				gui_constants.MONITOR_PATHS and all(gui_constants.MONITOR_PATHS):
				self.init_watchers()
			if gui_constants.FIRST_TIME_LEVEL != 2:
				normalize_first_time()
		if gui_constants.FIRST_TIME_LEVEL < 2:

			class FirstTime(file_misc.BasePopup):
				def __init__(self, parent=None):
					super().__init__(parent)
					main_layout = QVBoxLayout()
					info_lbl = QLabel("Hi there! Some big changes are about to occur!\n"+
					   "Please wait.. This will take at most a few minutes.\n"+
					   "If not then try restarting the application.")
					info_lbl.setAlignment(Qt.AlignCenter)
					main_layout.addWidget(info_lbl)
					prog = QProgressBar(self)
					prog.setMinimum(0)
					prog.setMaximum(0)
					prog.setTextVisible(False)
					main_layout.addWidget(prog)
					main_layout.addWidget(QLabel('Note: This popup will close itself when everything is ready'))
					self.main_widget.setLayout(main_layout)

			ft_widget = FirstTime(self)
			log_i('Invoking first time level 2')
			bridge = gallerydb.Bridge()
			thread = QThread(self)
			thread.setObjectName('Startup')
			bridge.moveToThread(thread)
			thread.started.connect(bridge.rebuild_galleries)
			bridge.DONE.connect(ft_widget.close)
			bridge.DONE.connect(self.setEnabled)
			bridge.DONE.connect(done)
			bridge.DONE.connect(bridge.deleteLater)
			thread.finished.connect(thread.deleteLater)
			thread.start()
			ft_widget.adjustSize()
			ft_widget.show()
			self.setEnabled(False)
		else:
			done()


	def initUI(self):
		self.center = QWidget()
		self.display = QStackedLayout()
		self.center.setLayout(self.display)
		# init the manga view variables
		self.manga_display()
		log_d('Create manga display: OK')
		# init the chapter view variables
		#self.chapter_display()
		self.m_l_view_index = self.display.addWidget(self.manga_list_main)
		self.m_t_view_index = self.display.addWidget(self.manga_table_view)
		# init toolbar
		self.init_toolbar()
		log_d('Create toolbar: OK')
		# init status bar
		self.init_stat_bar()
		log_d('Create statusbar: OK')

		self.system_tray = misc.SystemTray(QIcon(gui_constants.APP_ICO_PATH), self)
		gui_constants.SYSTEM_TRAY = self.system_tray
		tray_menu = QMenu(self)
		self.system_tray.setContextMenu(tray_menu)
		self.system_tray.setToolTip('Happypanda {}'.format(gui_constants.vs))
		tray_quit = QAction('Quit', tray_menu)
		tray_menu.addAction(tray_quit)
		tray_quit.triggered.connect(self.close)
		self.system_tray.show()
		log_d('Create system tray: OK')

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

		self.notification_bar = misc.NotificationOverlay(self)
		p = self.toolbar.pos()
		self.notification_bar.move(p.x(), p.y()+self.toolbar.height())
		self.notification_bar.resize(self.width())
		gui_constants.NOTIF_BAR = self.notification_bar
		log_d('Create notificationbar: OK')

		log_d('Window Create: OK')

	def _check_update(self):
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
					r = requests.get("https://raw.githubusercontent.com/Pewpews/happypanda/master/VS.txt",
					  verify='cacert.pem')
					a = r.text
					vs = a.strip()
					self.UPDATE_CHECK.emit(vs)
				except:
					log.exception('Checking Update: FAIL')
					self.UPDATE_CHECK.emit('this is a very long text which is is sure to be over limit')

		def check_update(vs):
			log_i('Received version: {}\nCurrent version: {}'.format(vs, gui_constants.vs))
			if vs != gui_constants.vs:
				if len(vs) < 10:
					self.notification_bar.add_text("Version {} of Happypanda is".format(vs)+
									   " available. Click here to update!", False)
					self.notification_bar.clicked.connect(lambda: utils.open_web_link(
						'https://github.com/Pewpews/happypanda/releases'))
					self.notification_bar.set_clickable(True)
				else:
					self.notification_bar.add_text("An error occurred while checking for new version")

		self.update_instance = upd_chk()
		thread = QThread(self)
		self.update_instance.moveToThread(thread)
		thread.started.connect(self.update_instance.fetch_vs)
		self.update_instance.UPDATE_CHECK.connect(check_update)
		self.update_instance.UPDATE_CHECK.connect(self.update_instance.deleteLater)
		thread.finished.connect(thread.deleteLater)
		thread.start()

	def _web_metadata_picker(self, gallery, title_url_list, queue, parent=None):
		if not parent:
			parent = self
		text = "Which gallery do you want to extract metadata from?"
		s_gallery_popup = misc.SingleGalleryChoices(gallery, title_url_list,
											  text, parent)
		s_gallery_popup.USER_CHOICE.connect(queue.put)

	def get_metadata(self, gal=None):
		thread = QThread(self)
		thread.setObjectName('App.get_metadata')
		fetch_instance = fetch.Fetch()
		if gal:
			galleries = [gal]
		else:
			if gui_constants.CONTINUE_AUTO_METADATA_FETCHER:
				galleries = [g for g in self.manga_list_view.gallery_model._data if not g.exed]
			else:
				galleries = self.manga_list_view.gallery_model._data
			if not galleries:
				self.notification_bar.add_text('Looks like we\'ve already gone through all galleries!')
				return None
		fetch_instance.galleries = galleries

		self.notification_bar.begin_show()
		fetch_instance.moveToThread(thread)

		def done(status):
			self.notification_bar.end_show()
			fetch_instance.deleteLater()

		fetch_instance.GALLERY_PICKER.connect(self._web_metadata_picker)
		fetch_instance.GALLERY_EMITTER.connect(self.manga_list_view.replace_edit_gallery)
		fetch_instance.AUTO_METADATA_PROGRESS.connect(self.notification_bar.add_text)
		thread.started.connect(fetch_instance.auto_web_metadata)
		fetch_instance.FINISHED.connect(done)
		thread.finished.connect(thread.deleteLater)
		thread.start()


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
		t = self.manga_list_view.gallery_model._data_count
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
		sett = settingsdialog.SettingsDialog(self)
		sett.scroll_speed_changed.connect(self.manga_list_view.updateGeometries)
		#sett.show()

	def init_toolbar(self):
		self.toolbar = QToolBar()
		self.toolbar.setFixedHeight(25)
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

		gallery_menu = QMenu()
		gallery_action = QToolButton()
		gallery_action.setText('Gallery ')
		gallery_action.setPopupMode(QToolButton.InstantPopup)
		gallery_action.setToolTip('Contains various gallery related features')
		gallery_action.setMenu(gallery_menu)
		add_gallery_icon = QIcon(gui_constants.PLUS_PATH)
		gallery_action_add = QAction(add_gallery_icon, "Add gallery", self)
		gallery_action_add.triggered.connect(self.manga_list_view.SERIES_DIALOG.emit)
		gallery_action_add.setToolTip('Add a single gallery thoroughly')
		gallery_menu.addAction(gallery_action_add)
		add_more_action = QAction(add_gallery_icon, "Add galleries...", self)
		add_more_action.setStatusTip('Add galleries from different folders')
		add_more_action.triggered.connect(lambda: self.populate(True))
		gallery_menu.addAction(add_more_action)
		populate_action = QAction(add_gallery_icon, "Populate from folder...", self)
		populate_action.setStatusTip('Populates the DB with galleries from a single folder')
		populate_action.triggered.connect(self.populate)
		gallery_menu.addAction(populate_action)
		gallery_menu.addSeparator()
		metadata_action = QAction('Get metadata for all galleries', self)
		metadata_action.triggered.connect(self.get_metadata)
		gallery_menu.addAction(metadata_action)
		self.toolbar.addWidget(gallery_action)
		self.toolbar.addSeparator()

		misc_action = QToolButton()
		misc_action.setText('Misc ')
		misc_action_menu = QMenu()
		misc_action.setMenu(misc_action_menu)
		misc_action.setPopupMode(QToolButton.InstantPopup)
		misc_action.setToolTip("Contains misc. features")
		misc_action_random = QAction("Open random gallery", misc_action_menu)
		misc_action_random.triggered.connect(self.manga_list_view.open_random_gallery)
		misc_action_menu.addAction(misc_action_random)
		duplicate_check_simple = QAction("Simple duplicate finder", misc_action_menu)
		duplicate_check_simple.triggered.connect(lambda: self.manga_list_view.duplicate_check())
		misc_action_menu.addAction(duplicate_check_simple)
		self.toolbar.addWidget(misc_action)

		spacer_middle = QWidget() # aligns buttons to the right
		spacer_middle.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
		self.toolbar.addWidget(spacer_middle)
		
		self.grid_toggle_g_icon = QIcon(gui_constants.GRID_PATH)
		self.grid_toggle_l_icon = QIcon(gui_constants.LIST_PATH)
		self.grid_toggle = QToolButton()
		if self.display.currentIndex() == self.m_l_view_index:
			self.grid_toggle.setIcon(self.grid_toggle_l_icon)
		else:
			self.grid_toggle.setIcon(self.grid_toggle_g_icon)
		self.grid_toggle.setObjectName('gridtoggle')
		self.grid_toggle.clicked.connect(self.toggle_view)
		self.toolbar.addWidget(self.grid_toggle)

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
		self.search_bar.setPlaceholderText("Search title, artist, namespace & tags")
		self.search_bar.setMinimumWidth(150)
		self.search_bar.setMaximumWidth(500)
		self.toolbar.addWidget(self.search_bar)
		self.toolbar.addSeparator()
		settings_icon = QIcon(gui_constants.SETTINGS_PATH)
		settings_action = QAction("Set&tings", self)
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
			data_thread = QThread(self)
			data_thread.setObjectName('General gallery populate')
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
								def append_to_model(x):
									self.manga_list_view.gallery_model.insertRows(x, None, len(x))

								class A(QObject):
									done = pyqtSignal()
									prog = pyqtSignal(int)
									def __init__(self, obj, parent=None):
										super().__init__(parent)
										self.obj = obj
										self.galleries = []

									def add_to_db(self):
										p = 0
										for x in self.obj:
											gallerydb.add_method_queue(
												gallerydb.GalleryDB.add_gallery_return, True, x)
											self.galleries.append(x)
											p += 1
											self.prog.emit(p)
										append_to_model(self.galleries)
										self.done.emit()

								loading.progress.setMaximum(len(gallery_list))
								a_instance = A(gallery_list)
								thread = QThread(self)
								thread.setObjectName('Database populate')
								def loading_show():
									loading.setText('Populating database.\nPlease wait...')
									loading.show()

								def loading_hide():
									loading.close()
									self.manga_list_view.gallery_model.ROWCOUNT_CHANGE.emit()

								def del_later():
									try:
										a_instance.deleteLater()
									except NameError:
										pass

								a_instance.moveToThread(thread)
								a_instance.prog.connect(loading.progress.setValue)
								thread.started.connect(loading_show)
								thread.started.connect(a_instance.add_to_db)
								a_instance.done.connect(loading_hide)
								a_instance.done.connect(del_later)
								thread.finished.connect(thread.deleteLater)
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
						log_e('Populating DB from gallery folder: Nothing was added!')
						loading.setText("<font color=red>Nothing was added. Check happypanda_log for details..</font>")
						loading.progress.setStyleSheet("background-color:red;")
						data_thread.quit
						QTimer.singleShot(10000, loading.close)

				def fetch_deleteLater():
					try:
						fetch_instance.deleteLater
					except NameError:
						pass

				def a_progress(prog):
					loading.progress.setValue(prog)
					loading.setText("Searching for galleries...")

				fetch_instance.moveToThread(data_thread)
				fetch_instance.DATA_COUNT.connect(loading.progress.setMaximum)
				fetch_instance.PROGRESS.connect(a_progress)
				data_thread.started.connect(fetch_instance.local)
				fetch_instance.FINISHED.connect(finished)
				fetch_instance.FINISHED.connect(fetch_deleteLater)
				data_thread.finished.connect(data_thread.deleteLater)
				data_thread.start()
				log_i('Populating DB from gallery folder')

	def resizeEvent(self, event):
		try:
			self.notification_bar.resize(event.size().width())
		except AttributeError:
			pass
		return super().resizeEvent(event)

	def closeEvent(self, event):
		# watchers
		try:
			self.watchers.stop_all()
		except AttributeError:
			pass

		# settings
		settings.set(self.manga_list_view.current_sort, 'General', 'current sort')
		settings.win_save(self, 'AppWindow')

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