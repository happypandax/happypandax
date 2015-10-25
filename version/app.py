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
						  QObject, QPoint, QPropertyAnimation)
from PyQt5.QtGui import (QPixmap, QIcon, QMoveEvent, QCursor,
						 QKeySequence)
from PyQt5.QtWidgets import (QApplication, QMainWindow, QListView,
							 QHBoxLayout, QFrame, QWidget, QVBoxLayout,
							 QLabel, QStackedLayout, QToolBar, QMenuBar,
							 QSizePolicy, QMenu, QAction, QLineEdit,
							 QSplitter, QMessageBox, QFileDialog,
							 QDesktopWidget, QPushButton, QCompleter,
							 QListWidget, QListWidgetItem, QToolTip,
							 QProgressBar, QToolButton, QSystemTrayIcon,
							 QShortcut, QGraphicsBlurEffect)

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
import misc_db

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical

class AppWindow(QMainWindow):
	"The application's main window"
	move_listener = pyqtSignal()
	db_activity_checker = pyqtSignal()
	graphics_blur = QGraphicsBlurEffect()
	def __init__(self):
		super().__init__()
		gui_constants.GENERAL_THREAD = QThread(self)
		gui_constants.GENERAL_THREAD.finished.connect(gui_constants.GENERAL_THREAD.deleteLater)
		gui_constants.GENERAL_THREAD.start()
		self.setAcceptDrops(True)
		self.initUI()
		self.start_up()
		QTimer.singleShot(3000, self._check_update)
		def test():
			self.manga_list_view.scrollToBottom()
		#QTimer.singleShot(10000, test)
		self.setFocusPolicy(Qt.NoFocus)
		self.set_shortcuts()
		self.graphics_blur.setParent(self)
		#ex = settings.ExProperties()
		#d = pewnet.ExHenManager(ex.ipb_id, ex.ipb_pass)
		#item = d.from_gallery_url('http://exhentai.org/g/861957/02741dc584/')
		#def a(): print(item.file)
		#if not item.file:
		#	item.file_rdy.connect(a)
		#else:
		#	a()

	def set_shortcuts(self):
		quit = QShortcut(QKeySequence('Ctrl+Q'), self, self.close)

	def init_watchers(self):

		def remove_gallery(g):
			index = self.manga_list_view.find_index(g.id, True)
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

	admin_db_method_invoker = pyqtSignal()
	def start_up(self):
		# TODO: Remove in beta
		level = 4
		def normalize_first_time():
			settings.set(level, 'Application', 'first time level')
			settings.save()

		def done(status=True):
			gallerydb.DatabaseEmitter.RUN = True
			if gui_constants.FIRST_TIME_LEVEL != level:
				normalize_first_time()
			if gui_constants.ENABLE_MONITOR and\
				gui_constants.MONITOR_PATHS and all(gui_constants.MONITOR_PATHS):
				self.init_watchers()
				if gui_constants.LOOK_NEW_GALLERY_STARTUP:
					if self.manga_list_view.gallery_model.db_emitter.count == gui_constants.GALLERY_DATA:
						self.scan_for_new_galleries()
					else:
						self.manga_list_view.gallery_model.db_emitter.DONE.connect(self.scan_for_new_galleries)
			self.download_manager = pewnet.Downloader()
			gui_constants.DOWNLOAD_MANAGER = self.download_manager
			self.download_manager.start_manager(4)

		if gui_constants.FIRST_TIME_LEVEL < 3:
			log_i('Invoking first time level {}'.format(level))
			app_widget = misc.ApplicationPopup(self)
			self.admin_db = gallerydb.AdminDB()
			self.admin_db.moveToThread(gui_constants.GENERAL_THREAD)
			self.admin_db.DONE.connect(done)
			self.admin_db.DONE.connect(self.admin_db.deleteLater)
			self.admin_db.DATA_COUNT.connect(app_widget.prog.setMaximum)
			self.admin_db.PROGRESS.connect(app_widget.prog.setValue)
			self.admin_db_method_invoker.connect(self.admin_db.rebuild_galleries)
			self.admin_db_method_invoker.connect(app_widget.show)
			app_widget.adjustSize()
			self.admin_db_method_invoker.emit()
		elif gui_constants.FIRST_TIME_LEVEL < 4:
			log_i('Invoking first time level {}'.format(level))
			settings.set([], 'Application', 'monitor paths')
			settings.set([], 'Application', 'ignore paths')
			gui_constants.MONITOR_PATHS = []
			gui_constants.IGNORE_PATHS = []
			settings.save()
			done()
		else:
			done()

	def initUI(self):
		self.center = QWidget()
		self.display = QStackedLayout()
		self._main_layout = QVBoxLayout()
		self._main_layout.setSpacing(0)
		self._main_layout.setContentsMargins(0,0,0,0)
		self._main_layout.addLayout(self.display)
		self.center.setLayout(self._main_layout)
		# init the manga view variables
		self.manga_display()
		log_d('Create manga display: OK')
		# init the chapter view variables
		#self.chapter_display()
		self.m_l_view_index = self.display.addWidget(self.manga_list_view)
		self.m_t_view_index = self.display.addWidget(self.manga_table_view)
		self.download_window = file_misc.GalleryDownloader(self)
		self.download_window.hide()
		# init toolbar
		self.init_toolbar()
		log_d('Create toolbar: OK')
		# init status bar
		self.init_stat_bar()
		log_d('Create statusbar: OK')

		self.tags_treeview = None
		if gui_constants.TAGS_TREEVIEW_ON_START:
			def tags_tree_none(): self.tags_treeview = None
			self.tags_treeview = misc_db.DBOverview(self, True)
			self.tags_treeview.about_to_close.connect(tags_tree_none)
			self.tags_treeview.show()

		self.system_tray = misc.SystemTray(QIcon(gui_constants.APP_ICO_PATH), self)
		gui_constants.SYSTEM_TRAY = self.system_tray
		tray_menu = QMenu(self)
		self.system_tray.setContextMenu(tray_menu)
		self.system_tray.setToolTip('Happypanda {}'.format(gui_constants.vs))
		tray_quit = QAction('Quit', tray_menu)
		tray_update = tray_menu.addAction('Check for update')
		tray_update.triggered.connect(self._check_update)
		tray_menu.addAction(tray_quit)
		tray_quit.triggered.connect(self.close)
		self.system_tray.show()
		self.system_tray.messageClicked.connect(self.showNormal)
		def tray_activate(r):
			if r == QSystemTrayIcon.Trigger:
				self.showNormal()
				self.activateWindow()
		self.system_tray.activated.connect(tray_activate)
		log_d('Create system tray: OK')
		#self.display.addWidget(self.chapter_main)

		self.setCentralWidget(self.center)
		self.setWindowIcon(QIcon(gui_constants.APP_ICO_PATH))


		props = settings.win_read(self, 'AppWindow')
		if props.resize:
			x, y = props.resize
			self.resize(x, y)
		else:
			self.resize(gui_constants.MAIN_W, gui_constants.MAIN_H)
		posx, posy = props.pos
		self.move(posx, posy)
		self.init_spinners()
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
					if gui_constants.DEBUG:
						r = requests.get("https://raw.githubusercontent.com/Pewpews/happypanda/master/VS.txt")
					else:
						r = requests.get("https://raw.githubusercontent.com/Pewpews/happypanda/master/VS.txt",
						  verify='cacert.pem')
					a = r.text
					vs = a.strip()
					self.UPDATE_CHECK.emit(vs)
				except:
					log.exception('Checking Update: FAIL')
					self.UPDATE_CHECK.emit('this is a very long text which is sure to be over limit')

		def check_update(vs):
			log_i('Received version: {}\nCurrent version: {}'.format(vs, gui_constants.vs))
			if vs != gui_constants.vs:
				if len(vs) < 10:
					self.notification_bar.begin_show()
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
		metadata_spinner = misc.Spinner(self)
		def move_md_spinner():
			metadata_spinner.update_move(
			QPoint(
				self.pos().x()+self.width()-65,
				self.pos().y()+self.toolbar.height()+55))
		metadata_spinner.set_text("Metadata")
		metadata_spinner.set_size(55)
		metadata_spinner.move(QPoint(self.pos().x()+self.width()-65,
							   self.pos().y()+self.toolbar.height()+55))
		self.move_listener.connect(move_md_spinner)
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

				class GalleryContextMenu(QMenu):
					app_instance = self
					error_galleries = status
					def __init__(self, parent=None):
						super().__init__(parent)
						self.error = [x for x in status if x[0].id]
						show_in_library_act = self.addAction('Show in library')
						show_in_library_act.triggered.connect(self.show_in_library)

					def show_in_library(self):
						viewer = self.app_instance.manga_list_view
						index = viewer.find_index(self.gallery_widget.gallery.id, True)
						if index:
							self.app_instance.manga_table_view.scroll_to_index(index)
							self.app_instance.manga_list_view.scroll_to_index(index)

				g_popup = file_misc.GalleryPopup(('Fecthing metadata for these galleries failed.'+
									  ' Check happypanda.log for details.', galleries), self, menu=GalleryContextMenu())
				g_popup.graphics_blur.setEnabled(False)
				close_button = g_popup.add_buttons('Close')[0]
				close_button.clicked.connect(g_popup.close)

		fetch_instance.GALLERY_PICKER.connect(self._web_metadata_picker)
		fetch_instance.GALLERY_EMITTER.connect(self.manga_list_view.replace_edit_gallery)
		fetch_instance.AUTO_METADATA_PROGRESS.connect(self.notification_bar.add_text)
		thread.started.connect(fetch_instance.auto_web_metadata)
		fetch_instance.FINISHED.connect(done)
		fetch_instance.FINISHED.connect(metadata_spinner.close)
		fetch_instance.FINISHED.connect(lambda: self.move_listener.disconnect(move_md_spinner))
		thread.finished.connect(thread.deleteLater)
		thread.start()
		metadata_spinner.show()

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
		self.manga_list_view.gallery_model.db_emitter.COUNT_CHANGE.connect(self.stat_row_info)
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
		t = self.manga_list_view.gallery_model.db_emitter.count
		self.stat_info.setText("Loaded {} of {} ".format(r, t))

	def manga_display(self):
		"initiates the manga view and related things"
		#list view
		self.manga_list_view = gallery.MangaView(self)
		self.manga_list_view.clicked.connect(self.popup)
		self.manga_list_view.manga_delegate.POPUP.connect(self.popup)
		self.popup_window = misc.GalleryMetaWindow(self)
		self.popup_window.arrow_size = (10,10)

		#table view

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


	def init_spinners(self):
		# fetching spinner
		self.data_fetch_spinner = misc.Spinner(self)
		self.data_fetch_spinner.set_size(60)
		self.move_listener.connect(
			lambda: self.data_fetch_spinner.update_move(
				QPoint(self.pos().x()+self.width()//2, self.pos().y()+self.height()//2)))
		
		self.manga_list_view.gallery_model.ADD_MORE.connect(self.data_fetch_spinner.show)
		self.manga_list_view.gallery_model.db_emitter.START.connect(self.data_fetch_spinner.show)
		self.manga_list_view.gallery_model.ADDED_ROWS.connect(self.data_fetch_spinner.before_hide)

		## deleting spinner
		#self.gallery_delete_spinner = misc.Spinner(self)
		#self.gallery_delete_spinner.set_size(40,40)
		##self.gallery_delete_spinner.set_text('Removing...')
		#self.manga_list_view.gallery_model.rowsAboutToBeRemoved.connect(self.gallery_delete_spinner.show)
		#self.manga_list_view.gallery_model.rowsRemoved.connect(self.gallery_delete_spinner.before_hide)


	def search(self, srch_string):
		self.search_bar.setText(srch_string)
		self.search_backward.setVisible(True)
		self.manga_list_view.sort_model.init_search(srch_string)

	def popup(self, index):
		if not self.popup_window.isVisible():
			#self.popup_window.set_gallery(index.data(Qt.UserRole+1))
			m_x = QCursor.pos().x()
			m_y = QCursor.pos().y()
			d_w = QDesktopWidget().width()
			d_h = QDesktopWidget().height()
			p_w = self.popup_window.width()
			p_h = self.popup_window.height()
			
			index_rect = self.manga_list_view.visualRect(index)
			index_point = self.manga_list_view.mapToGlobal(index_rect.topRight())
			index_point_btm = self.manga_list_view.mapToGlobal(index_rect.bottomRight())
			# adjust so it doesn't go offscreen
			#if d_w - m_x < p_w and d_h - m_y < p_h: # bottom
			#	self.popup_window.move(m_x-p_w+5, m_y-p_h)
			#elif d_w - m_x > p_w and d_h - m_y < p_h:
			#	self.popup_window.move(m_x+5, m_y-p_h)
			#elif d_w - m_x < p_w:
			#	self.popup_window.move(m_x-p_w+5, m_y+5)
			#else:
			#	self.popup_window.move(index_point)

			self.popup_window.show_gallery(index, self.manga_list_view)

	def favourite_display(self):
		"Switches to favourite display"
		self.manga_table_view.sort_model.fav_view()
		self.favourite_btn.selected = True
		self.library_btn.selected = False

	def catalog_display(self):
		"Switches to catalog display"
		self.manga_table_view.sort_model.catalog_view()
		self.library_btn.selected = True
		self.favourite_btn.selected = False

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
		self.toolbar.setIconSize(QSize(20,20))

		spacer_start = QWidget() # aligns the first actions properly
		spacer_start.setFixedSize(QSize(10, 1))
		self.toolbar.addWidget(spacer_start)

		self.favourite_btn = misc.ToolbarButton(self.toolbar, 'Favorites')
		self.toolbar.addWidget(self.favourite_btn)
		self.favourite_btn.clicked.connect(self.favourite_display) #need lambda to pass extra args

		self.library_btn = misc.ToolbarButton(self.toolbar, 'Library')
		self.library_btn.setFixedWidth(60)
		self.toolbar.addWidget(self.library_btn)
		self.library_btn.clicked.connect(self.catalog_display) #need lambda to pass extra args
		self.library_btn.selected = True

		self.toolbar.addSeparator()

		gallery_menu = QMenu()
		gallery_action = QToolButton()
		gallery_action.setText('Gallery ')
		gallery_action.setPopupMode(QToolButton.InstantPopup)
		gallery_action.setToolTip('Contains various gallery related features')
		gallery_action.setMenu(gallery_menu)
		add_gallery_icon = QIcon(gui_constants.PLUS_PATH)
		gallery_action_add = QAction(add_gallery_icon, "Add single gallery...", self)
		gallery_action_add.triggered.connect(self.manga_list_view.SERIES_DIALOG.emit)
		gallery_action_add.setToolTip('Add a single gallery thoroughly')
		gallery_menu.addAction(gallery_action_add)
		add_more_action = QAction(add_gallery_icon, "Add galleries...", self)
		add_more_action.setStatusTip('Add galleries from different folders')
		add_more_action.triggered.connect(lambda: self.populate(True))
		gallery_menu.addAction(add_more_action)
		populate_action = QAction(add_gallery_icon, "Populate from directory/archive...", self)
		populate_action.setStatusTip('Populates the DB with galleries from a single folder or archive')
		populate_action.triggered.connect(self.populate)
		gallery_menu.addAction(populate_action)
		gallery_menu.addSeparator()
		metadata_action = QAction('Get metadata for all galleries', self)
		metadata_action.triggered.connect(self.get_metadata)
		gallery_menu.addAction(metadata_action)
		scan_galleries_action = QAction('Scan for new galleries', self)
		scan_galleries_action.triggered.connect(self.scan_for_new_galleries)
		scan_galleries_action.setStatusTip('Scan monitored folders for new galleries')
		gallery_menu.addAction(scan_galleries_action)
		self.toolbar.addWidget(gallery_action)


		misc_action = QToolButton()
		misc_action.setText('Tools ')
		misc_action_menu = QMenu()
		misc_action.setMenu(misc_action_menu)
		misc_action.setPopupMode(QToolButton.InstantPopup)
		misc_action.setToolTip("Contains misc. features")
		gallery_downloader = QAction("Gallery Downloader", misc_action_menu)
		gallery_downloader.triggered.connect(self.download_window.show)
		misc_action_menu.addAction(gallery_downloader)
		duplicate_check_simple = QAction("Simple Duplicate Finder", misc_action_menu)
		duplicate_check_simple.triggered.connect(lambda: self.manga_list_view.duplicate_check())
		misc_action_menu.addAction(duplicate_check_simple)
		misc_action_random = QAction("Random Gallery Opener", misc_action_menu)
		misc_action_random.triggered.connect(self.manga_list_view.open_random_gallery)
		misc_action_menu.addAction(misc_action_random)
		self.toolbar.addWidget(misc_action)

		spacer_middle = QWidget() # aligns buttons to the right
		spacer_middle.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
		self.toolbar.addWidget(spacer_middle)


		sort_action = QToolButton()
		sort_action.setIcon(QIcon(gui_constants.SORT_PATH))
		sort_action.setMenu(misc.SortMenu(self.toolbar, self.manga_list_view))
		sort_action.setPopupMode(QToolButton.InstantPopup)
		self.toolbar.addWidget(sort_action)
		
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

		spacer_mid2 = QWidget()
		spacer_mid2.setFixedSize(QSize(5, 1))
		self.toolbar.addWidget(spacer_mid2)

		self.search_bar = misc.LineEdit()
		self.search_bar.setObjectName('search_bar')
		self.search_timer = QTimer(self)
		self.search_timer.setSingleShot(True)
		self.search_timer.timeout.connect(lambda: self.search(self.search_bar.text()))

		if gui_constants.SEARCH_AUTOCOMPLETE:
			completer = QCompleter(self)
			completer_view = misc.CompleterPopupView()
			completer.setPopup(completer_view)
			completer_view._setup()
			completer.setModel(self.manga_list_view.gallery_model)
			completer.setCaseSensitivity(Qt.CaseInsensitive)
			completer.setCompletionMode(QCompleter.PopupCompletion)
			completer.setCompletionRole(Qt.DisplayRole)
			completer.setCompletionColumn(gui_constants.TITLE)
			completer.setFilterMode(Qt.MatchContains)
			self.search_bar.setCompleter(completer)
			self.search_bar.returnPressed.connect(lambda: self.search(self.search_bar.text()))
		if not gui_constants.SEARCH_ON_ENTER:
			self.search_bar.textEdited.connect(lambda: self.search_timer.start(800))
		self.search_bar.setPlaceholderText("Search title, artist, namespace & tags")
		self.search_bar.setMinimumWidth(150)
		self.search_bar.setMaximumWidth(500)
		self.search_bar.setFixedHeight(19)
		self.manga_list_view.sort_model.HISTORY_SEARCH_TERM.connect(lambda a: self.search_bar.setText(a))
		self.toolbar.addWidget(self.search_bar)

		def search_history(_, back=True): # clicked signal passes a bool
			sort_model =  self.manga_list_view.sort_model
			nav = sort_model.PREV if back else sort_model.NEXT
			history_term = sort_model.navigate_history(nav)
			if back:
				self.search_forward.setVisible(True)

		back = QShortcut(QKeySequence(QKeySequence.Back), self, lambda: search_history(None))
		forward = QShortcut(QKeySequence(QKeySequence.Forward), self, lambda: search_history(None, False))

		search_backbutton = QToolButton(self.toolbar)
		search_backbutton.setText(u'\u25C0')
		search_backbutton.setFixedWidth(15)
		search_backbutton.clicked.connect(search_history)
		self.search_backward = self.toolbar.addWidget(search_backbutton)
		self.search_backward.setVisible(False)
		search_forwardbutton = QToolButton(self.toolbar)
		search_forwardbutton.setText(u'\u25B6')
		search_forwardbutton.setFixedWidth(15)
		search_forwardbutton.clicked.connect(lambda: search_history(None, False))
		self.search_forward = self.toolbar.addWidget(search_forwardbutton)
		self.search_forward.setVisible(False)

		spacer_end = QWidget() # aligns settings action properly
		spacer_end.setFixedSize(QSize(10, 1))
		self.toolbar.addWidget(spacer_end)

		settings_act = QToolButton(self.toolbar)
		settings_act.setIcon(QIcon(gui_constants.SETTINGS_PATH))
		settings_act.clicked.connect(self.settings)
		self.toolbar.addWidget(settings_act)

		spacer_end2 = QWidget() # aligns About action properly
		spacer_end2.setFixedSize(QSize(5, 1))
		self.toolbar.addWidget(spacer_end2)
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
			msg_box = misc.BasePopup(self)
			l = QVBoxLayout()
			msg_box.main_widget.setLayout(l)
			l.addWidget(QLabel('Directory or Archive?'))
			l.addLayout(msg_box.buttons_layout)

			def from_dir():
				path = QFileDialog.getExistingDirectory(self, "Choose a directory containing your galleries")
				if not path:
					return
				msg_box.close()
				gui_constants.OVERRIDE_SUBFOLDER_AS_GALLERY = True
				self.gallery_populate(path, True)
			def from_arch():
				path = QFileDialog.getOpenFileName(self, 'Choose an archive containing your galleries',
									   filter=utils.FILE_FILTER)
				path = [path[0]]
				if not all(path) or not path:
					return
				msg_box.close()
				gui_constants.OVERRIDE_SUBFOLDER_AS_GALLERY = True
				self.gallery_populate(path, True)

			buttons = msg_box.add_buttons('Directory', 'Archive', 'Close')
			buttons[2].clicked.connect(msg_box.close)
			buttons[0].clicked.connect(from_dir)
			buttons[1].clicked.connect(from_arch)
			msg_box.adjustSize()
			msg_box.show()

	def gallery_populate(self, path, validate=False):
		"Scans the given path for gallery to add into the DB"
		if len(path) is not 0:
			data_thread = QThread(self)
			data_thread.setObjectName('General gallery populate')
			loading = misc.Loading(self)
			self.g_populate_inst = fetch.Fetch()
			self.g_populate_inst.series_path = path
			loading.show()

			def finished(status):
				def hide_loading():
					loading.hide()
				if status:
					if len(status) != 0:
						def add_gallery(gallery_list):
							def append_to_model(x):
								self.manga_list_view.sort_model.insertRows(x, None, len(x))
								self.manga_list_view.sort_model.init_search(
									self.manga_list_view.sort_model.current_term)

							class A(QObject):
								done = pyqtSignal()
								prog = pyqtSignal(int)
								def __init__(self, obj, parent=None):
									super().__init__(parent)
									self.obj = obj
									self.galleries = []

								def add_to_db(self):
									for y, x in enumerate(self.obj):
										gallerydb.add_method_queue(
											gallerydb.GalleryDB.add_gallery_return, False, x)
										self.galleries.append(x)
										y += 1
										self.prog.emit(y)
									append_to_model(self.galleries)
									self.done.emit()
							loading.progress.setMaximum(len(gallery_list))
							self.a_instance = A(gallery_list)
							thread = QThread(self)
							thread.setObjectName('Database populate')
							def loading_show(numb):
								if loading.isHidden():
									loading.show()
								loading.setText('Populating database ({}/{})\nPlease wait...'.format(
									numb, loading.progress.maximum()))
								loading.progress.setValue(numb)
								loading.show()

							def loading_hide():
								loading.close()
								self.manga_list_view.gallery_model.ROWCOUNT_CHANGE.emit()

							self.a_instance.moveToThread(thread)
							self.a_instance.prog.connect(loading_show)
							thread.started.connect(self.a_instance.add_to_db)
							self.a_instance.done.connect(loading_hide)
							self.a_instance.done.connect(self.a_instance.deleteLater)
							#a_instance.add_to_db()
							thread.finished.connect(thread.deleteLater)
							thread.start()
						#data_thread.quit
						hide_loading()
						log_i('Populating DB from gallery folder: OK')
						if validate:
							gallery_list = misc.GalleryListView(self)
							gallery_list.SERIES.connect(add_gallery)
							for ser in status:
								if ser.is_archive and gui_constants.SUBFOLDER_AS_GALLERY:
									p = os.path.split(ser.path)[1]
									if ser.chapters[0].path:
										pt_in_arch = os.path.split(ser.path_in_archive)
										pt_in_arch = pt_in_arch[1] or pt_in_arch[0]
										text = '{}: {}'.format(p, pt_in_arch)
									else:
										text = p
									gallery_list.add_gallery(ser, text)
								else:
									gallery_list.add_gallery(ser, os.path.split(ser.path)[1])
							#self.manga_list_view.gallery_model.populate_data()
							gallery_list.update_count()
							gallery_list.show()
						else:
							add_gallery(status)
					else:
						log_d('No new gallery was found')
						loading.setText("No new gallery found")
						#data_thread.quit

				else:
					log_e('Populating DB from gallery folder: Nothing was added!')
					loading.setText("<font color=red>Nothing was added. Check happypanda_log for details..</font>")
					loading.progress.setStyleSheet("background-color:red;")
					data_thread.quit
					QTimer.singleShot(8000, loading.close)

			def skipped_gs(s_list):
				"Skipped galleries"
				msg_box = QMessageBox(self)
				msg_box.setIcon(QMessageBox.Question)
				msg_box.setText('Do you want to view skipped paths?')
				msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
				msg_box.setDefaultButton(QMessageBox.No)
				if msg_box.exec() == QMessageBox.Yes:
					list_wid = QListWidget(self)
					for g in s_list:
						list_wid.addItem(g)
					list_wid.setWindowTitle('{} skipped paths'.format(len(s_list)))
					list_wid.setWindowFlags(Qt.Window)
					list_wid.resize(500,500)
					list_wid.show()

			def a_progress(prog):
				loading.progress.setValue(prog)
				loading.setText("Searching for galleries...")

			self.g_populate_inst.moveToThread(data_thread)
			self.g_populate_inst.DATA_COUNT.connect(loading.progress.setMaximum)
			self.g_populate_inst.PROGRESS.connect(a_progress)
			self.g_populate_inst.FINISHED.connect(finished)
			self.g_populate_inst.FINISHED.connect(self.g_populate_inst.deleteLater)
			self.g_populate_inst.SKIPPED.connect(skipped_gs)
			data_thread.finished.connect(data_thread.deleteLater)
			data_thread.started.connect(self.g_populate_inst.local)
			data_thread.start()
			#fetch_instance.local()
			log_i('Populating DB from directory/archive')

	def scan_for_new_galleries(self):
		available_folders =  gui_constants.ENABLE_MONITOR and\
									gui_constants.MONITOR_PATHS and all(gui_constants.MONITOR_PATHS)
		if available_folders and not gui_constants.SCANNING_FOR_GALLERIES:
			gui_constants.SCANNING_FOR_GALLERIES = True
			self.notification_bar.add_text("Scanning for new galleries...")
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
							if os.path.exists(p):
								dir_content = scandir.scandir(p)
								for d in dir_content:
									paths.append(d.path)
							else:
								log_e("Monitored path does not exists: {}".format(p.encode(errors='ignore')))

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
										g.profile = utils.get_gallery_img(g.chapters[0].path, g.path)
									else:
										g.profile = utils.get_gallery_img(g.chapters[0].path)
									if not g.profile:
										raise Exception
								except:
									g.profile = gui_constants.NO_IMAGE_PATH
							
								galleries.append(g)
								final_paths.append(g.path)
						self.final_paths_and_galleries.emit(final_paths, galleries)
						self.finished.emit()
						self.deleteLater()
					#if gui_constants.LOOK_NEW_GALLERY_AUTOADD:
					#	QTimer.singleShot(10000, self.gallery_populate(final_paths))
					#	return

				def show_new_galleries(final_paths, galleries):
					if final_paths and galleries:
						gui_constants.OVERRIDE_MOVE_IMPORTED_IN_FETCH = True
						if gui_constants.LOOK_NEW_GALLERY_AUTOADD:
							self.gallery_populate(final_paths)
						else:

							class NewGalleryMenu(QMenu):

								def __init__(self, parent=None):
									super().__init__(parent)

									ignore_act = self.addAction('Add to ignore list')
									ignore_act.triggered.connect(self.add_to_ignore)

								def add_to_ignore(self):
									gallery = self.gallery_widget.gallery
									gui_constants.IGNORE_PATHS.append(gallery.path)
									settings.set(gui_constants.IGNORE_PATHS, 'Application', 'ignore paths')
									if self.gallery_widget.parent_widget.gallery_layout.count() == 1:
										self.gallery_widget.parent_widget.close()
									else:
										self.gallery_widget.close()

							if len(galleries) == 1:
								self.notification_bar.add_text("{} new gallery was discovered in one of your monitored directories".format(len(galleries)))
							else:
								self.notification_bar.add_text("{} new galleries were discovered in one of your monitored directories".format(len(galleries)))
							text = "These new galleries were discovered! Do you want to add them?"\
								if len(galleries) > 1 else "This new gallery was discovered! Do you want to add it?"
							g_popup = file_misc.GalleryPopup((text, galleries), self, NewGalleryMenu())
							buttons = g_popup.add_buttons('Add', 'Close')

							def populate_n_close():
								g_popup.close()
								self.gallery_populate(final_paths)
							buttons[0].clicked.connect(populate_n_close)
							buttons[1].clicked.connect(g_popup.close)

				def finished(): gui_constants.SCANNING_FOR_GALLERIES = False

				thread = QThread(self)
				self.scan_inst = ScanDir()
				self.scan_inst.moveToThread(thread)
				self.scan_inst.final_paths_and_galleries.connect(show_new_galleries)
				self.scan_inst.finished.connect(finished)
				thread.started.connect(self.scan_inst.scan_dirs)
				#self.scan_inst.scan_dirs()
				thread.finished.connect(thread.deleteLater)
				thread.start()
			except:
				self.notification_bar.add_text('An error occured while attempting to scan for new galleries. Check happypanda.log.')
				log.exception('An error occured while attempting to scan for new galleries.')
				gui_constants.SCANNING_FOR_GALLERIES = False

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
			if os.path.isdir(path) or path.endswith(utils.ARCHIVE_FILES):
				acceptable.append(path)
			else:
				unaccept.append(path)
		log_i('Acceptable dropped items: {}'.format(len(acceptable)))
		log_i('Unacceptable dropped items: {}'.format(len(unaccept)))
		log_d('Dropped items: {}\n{}'.format(acceptable, unaccept).encode(errors='ignore'))
		if acceptable:
			self.notification_bar.add_text('Adding dropped items...')
			log_i('Adding dropped items')
			l = len(acceptable) == 1
			f_item = acceptable[0]
			if f_item.endswith(utils.ARCHIVE_FILES):
				f_item = utils.check_archive(f_item)
			else:
				f_item = utils.recursive_gallery_check(f_item)
			f_item_l = len(f_item) < 2
			subfolder_as_c = not gui_constants.SUBFOLDER_AS_GALLERY
			if l and subfolder_as_c or l and f_item_l:
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
		self.move_listener.emit()
		return super().resizeEvent(event)

	def moveEvent(self, event):
		self.move_listener.emit()
		return super().moveEvent(event)

	def showEvent(self, event):
		return super().showEvent(event)

	def closeEvent(self, event):
		self.system_tray.hide()
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

		if self.tags_treeview:
			self.tags_treeview.close()
		self.download_window.close()

		# check if there is db activity
		if not gallerydb.method_queue.empty():
			class DBActivityChecker(QObject):
				FINISHED = pyqtSignal()
				def __init__(self, **kwargs):
					super().__init__(**kwargs)

				def check(self):
					gallerydb.method_queue.join()
					self.FINISHED.emit()
					self.deleteLater()

			db_activity = DBActivityChecker()
			db_spinner = misc.Spinner(self)
			self.db_activity_checker.connect(db_activity.check)
			db_activity.moveToThread(gui_constants.GENERAL_THREAD)
			db_activity.FINISHED.connect(db_spinner.close)
			db_spinner.set_size(50)
			db_spinner.set_text('Activity')
			db_spinner.move(QPoint(self.pos().x()+self.width()-70, self.pos().y()+self.height()-70))
			self.move_listener.connect(lambda: db_spinner.update_move(QPoint(self.pos().x()+self.width()-70,
																	self.pos().y()+self.height()-70)))
			db_spinner.show()
			self.db_activity_checker.emit()
			msg_box = QMessageBox(self)
			msg_box.setText('Database activity detected!')
			msg_box.setInformativeText("Closing now might result in data loss." +
								 " Do you still want to close?\n(Wait for the activity spinner to hide before closing)")
			msg_box.setIcon(QMessageBox.Critical)
			msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
			msg_box.setDefaultButton(QMessageBox.No)
			if msg_box.exec() == QMessageBox.Yes:
				log_d('Force Exit App: OK')
				super().closeEvent(event)
			else:
				log_d('Ignore Exit App')
				event.ignore()
		else:
			log_d('Normal Exit App: OK')
			super().closeEvent(event)

if __name__ == '__main__':
	raise NotImplementedError("Unit testing not implemented yet!")