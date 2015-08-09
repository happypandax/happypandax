#"""
#This file is part of Happypanda.
#Happypanda is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 2 of the License, or
#any later version.
#Happypanda is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#You should have received a copy of the GNU General Public License
#along with Happypanda.  If not, see <http://www.gnu.org/licenses/>.
#"""

import sys, logging, os, threading, re, requests, scandir
from PyQt5.QtCore import (Qt, QSize, pyqtSignal, QThread, QEvent, QTimer,
						  QObject)
from PyQt5.QtGui import (QPixmap, QIcon, QMoveEvent, QCursor)
from PyQt5.QtWidgets import (QApplication, QMainWindow, QListView,
							 QHBoxLayout, QFrame, QWidget, QVBoxLayout,
							 QLabel, QStackedLayout, QToolBar, QMenuBar,
							 QSizePolicy, QMenu, QAction, QLineEdit,
							 QSplitter, QMessageBox, QFileDialog,
							 QDesktopWidget, QPushButton, QCompleter,
							 QListWidget, QListWidgetItem, QToolTip,
							 QProgressBar, QToolButton, QSystemTrayIcon)

import gui_constants
import misc
import gallery
import file_misc
import settingsdialog
import gallerydialog
import fetch
import gallerydb
import settings
import pewnet
import utils

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical

class AppWindow(QMainWindow):
	"The application's main window"
	move_listener = pyqtSignal()
	def __init__(self):
		super().__init__()
		self.setAcceptDrops(True)
		self.initUI()
		self.start_up()
		QTimer.singleShot(3000, self._check_update)
		self.setFocusPolicy(Qt.NoFocus)

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
					finished = pyqtSignal()
					def __init__(self, parent=None):
						super().__init__(parent)
						self.scanned_data = []
					def scan_dirs(self):
						paths = []
						for p in gui_constants.MONITOR_PATHS:
							dir_content = scandir.scandir(p)
							for d in dir_content:
								paths.append(d.path)

						fetch_inst = fetch.Fetch(self)
						fetch_inst.series_path = paths
						def set_scanned_d(d):
							self.scanned_data = d
						fetch_inst.FINISHED.connect(set_scanned_d)
						fetch_inst.local()
						#contents = []
						#for g in self.scanned_data:
						#	contents.append(g)

						#paths = sorted(paths)
						#new_galleries = []
						#for x in contents:
						#	y = utils.b_search(paths, os.path.normcase(x.path))
						#	if not y:
						#		new_galleries.append(x)

						galleries = []
						final_paths = []
						if self.scanned_data:
							for g in self.scanned_data:
								try:
									if g.is_archive:
										g.profile = utils.get_gallery_img(g.chapters[0], g.path)
									else:
										g.profile = utils.get_gallery_img(g.chapters[0])
								except:
									g.profile = gui_constants.NO_IMAGE_PATH
							
								galleries.append(g)
								final_paths.append(g.path)
						self.final_paths_and_galleries.emit(final_paths, galleries)
						self.finished.emit()
					#if gui_constants.LOOK_NEW_GALLERY_AUTOADD:
					#	QTimer.singleShot(10000, self.gallery_populate(final_paths))
					#	return

				def show_new_galleries(final_paths, galleries):
					if final_paths and galleries:
						gui_constants.OVERRIDE_MOVE_IMPORTED_IN_FETCH = True
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
				self.scan_inst = ScanDir()
				self.scan_inst.moveToThread(thread)
				self.scan_inst.final_paths_and_galleries.connect(show_new_galleries)
				self.scan_inst.final_paths_and_galleries.connect(lambda a: self.scan_inst.deleteLater())
				thread.started.connect(self.scan_inst.scan_dirs)
				#self.scan_inst.scan_dirs()
				thread.finished.connect(thread.deleteLater)
				thread.start()
			except:
				self.notification_bar.add_text('An error occured while attempting to scan for new galleries. Check happypanda.log.')
				log.exception('An error occured while attempting to scan for new galleries.')

	def start_up(self):
		def normalize_first_time():
			settings.set(3, 'Application', 'first time level')
			settings.save()
		def done(status=True):
			if gui_constants.FIRST_TIME_LEVEL != 3:
				normalize_first_time()
			self.manga_list_view.gallery_model.init_data()
			if gui_constants.ENABLE_MONITOR and\
				gui_constants.MONITOR_PATHS and all(gui_constants.MONITOR_PATHS):
				self.init_watchers()
		if gui_constants.FIRST_TIME_LEVEL < 3:

			class FirstTime(misc.BasePopup):
				def __init__(self, parent=None):
					super().__init__(parent)
					main_layout = QVBoxLayout()
					info_lbl = QLabel("Hi there! I need to rebuild your galleries.\n"+
					   "Please wait.. Restart if there is no sign of progress.")
					info_lbl.setAlignment(Qt.AlignCenter)
					main_layout.addWidget(info_lbl)
					self.prog = QProgressBar(self)
					main_layout.addWidget(self.prog)
					main_layout.addWidget(QLabel('Note: This popup will close itself when everything is ready'))
					self.main_widget.setLayout(main_layout)

			ft_widget = FirstTime(self)
			log_i('Invoking first time level 3')
			bridge = gallerydb.Bridge()
			thread = QThread(self)
			thread.setObjectName('Startup')
			bridge.moveToThread(thread)
			thread.started.connect(bridge.rebuild_galleries)
			bridge.DONE.connect(ft_widget.close)
			bridge.DONE.connect(self.setEnabled)
			bridge.DONE.connect(done)
			bridge.DONE.connect(bridge.deleteLater)
			bridge.DATA_COUNT.connect(ft_widget.prog.setMaximum)
			bridge.PROGRESS.connect(ft_widget.prog.setValue)
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
			if not isinstance(gal, list):
				galleries = [gal]
			else:
				galleries = gal
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
			if not isinstance(status, bool):
				galleries = []
				for tup in status:
					galleries.append(tup[0])
				g_popup = file_misc.GalleryPopup(('Fecthing metadata for these galleries failed.'+
									  ' Check happypanda.log for details.', galleries), self)
				close_button = g_popup.add_buttons('Close')[0]
				close_button.clicked.connect(g_popup.close)

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
										gui_constants.NOTIF_BAR.begin_show()
										gui_constants.NOTIF_BAR.add_text('Populating database...')
										for y, x in enumerate(self.obj):
											gui_constants.NOTIF_BAR.add_text('Populating database {}/{}'.format(y+1, len(self.obj)))
											gallerydb.add_method_queue(
												gallerydb.GalleryDB.add_gallery_return, False, x)
											self.galleries.append(x)
											y += 1
											self.prog.emit(y)
										append_to_model(self.galleries)
										gui_constants.NOTIF_BAR.end_show()
										self.done.emit()

								loading.progress.setMaximum(len(gallery_list))
								a_instance = A(gallery_list)
								thread = QThread(self)
								thread.setObjectName('Database populate')
								def loading_show():
									loading.setText('Populating database.\nPlease wait...')
									loading.show()

								def loading_hide():
									loading.hide()
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
								#a_instance.add_to_db()
							#data_thread.quit
							hide_loading()
							log_i('Populating DB from gallery folder: OK')
							if validate:
								gallery_list = misc.GalleryListView(self)
								gallery_list.SERIES.connect(add_gallery)
								for ser in status:
									if ser.is_archive and gui_constants.SUBFOLDER_AS_GALLERY:
										p = os.path.split(ser.path)[1]
										if ser.chapters[0]:
											text = '{}: {}'.format(p, os.path.split(ser.chapters[0])[0])
										else:
											text = p
										gallery_list.add_gallery(ser, text)
									else:
										gallery_list.add_gallery(ser, os.path.split(ser.path)[1])
								#self.manga_list_view.gallery_model.populate_data()
								gallery_list.show()
							else:
								add_gallery(status)
							misc.Loading.ON = False
						else:
							log_d('No new gallery was found')
							loading.setText("No new gallery found")
							#data_thread.quit
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

				#fetch_instance.moveToThread(data_thread)
				fetch_instance.DATA_COUNT.connect(loading.progress.setMaximum)
				fetch_instance.PROGRESS.connect(a_progress)
				#data_thread.started.connect(fetch_instance.local)
				fetch_instance.FINISHED.connect(finished)
				fetch_instance.FINISHED.connect(fetch_deleteLater)
				#data_thread.finished.connect(data_thread.deleteLater)
				#data_thread.start()
				fetch_instance.local()
				log_i('Populating DB from gallery folder')

	def dragEnterEvent(self, event):
		if event.mimeData().hasUrls():
			event.acceptProposedAction()
		else:
			self.notification_bar.add_text('File is not supported')

	def dropEvent(self, event):
		acceptable = []
		unaccept = []
		for u in event.mimeData().urls():
			path = u.toLocalFile()
			if os.path.isdir(path):
				acceptable.append(path)
				continue
			head, tail = os.path.split(path)
			if tail.endswith(utils.ARCHIVE_FILES):
				acceptable.append(path)
			else:
				unaccept(path)
		log_i('Acceptable dropped items: {}'.format(len(acceptable)))
		log_i('Unacceptable dropped items: {}'.format(len(unaccept)))
		log_d('Dropped items: {}\n{}'.format(acceptable, unaccept).encode(errors='ignore'))
		if acceptable:
			self.notification_bar.add_text('Adding dropped items...')
			log_i('Adding dropped items')
			if len(acceptable) == 1:
				g_d = gallerydialog.GalleryDialog(self, acceptable[0])
				g_d.SERIES.connect(self.manga_list_view.gallery_model.addRows)
				g_d.show()
			else:
				self.gallery_populate(acceptable, True)
		else:
			text = 'File not supported' if len(unaccept) < 2 else 'Files not supported'
			self.notification_bar.add_text(text)

		if unaccept:
			self.notification_bar.add_text('Some unsupported files did not get added')

	def resizeEvent(self, event):
		try:
			self.notification_bar.resize(event.size().width())
		except AttributeError:
			pass
		return super().resizeEvent(event)

	def moveEvent(self, event):
		self.move_listener.emit()
		return super().moveEvent(event)

	def closeEvent(self, event):
		# watchers
		try:
			self.watchers.stop_all()
		except AttributeError:
			pass

		# settings
		settings.set(self.manga_list_view.current_sort, 'General', 'current sort')
		settings.set(gui_constants.IGNORE_PATHS, 'Application', 'ignore paths')
		settings.win_save(self, 'AppWindow')

		# temp dir
		try:
			for root, dirs, files in scandir.walk('temp', topdown=False):
				for name in files:
					os.remove(os.path.join(root, name))
				for name in dirs:
					os.rmdir(os.path.join(root, name))
			log_d('Flush temp on exit: OK')
		except:
			log.exception('Flush temp on exit: FAIL')
		log_d('Normal Exit App: OK')
		super().closeEvent(event)
		#app = QApplication.instance()
		#app.exit()
		#sys.exit()

if __name__ == '__main__':
	raise NotImplementedError("Unit testing not implemented yet!")