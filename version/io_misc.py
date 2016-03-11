import logging, os, json, datetime, random, re

from watchdog.events import FileSystemEventHandler, DirDeletedEvent
from watchdog.observers import Observer
from threading import Timer

from PyQt5.QtCore import (Qt, QObject, pyqtSignal, QTimer, QSize, QThread)
from PyQt5.QtGui import (QPixmap, QIcon, QColor, QTextOption, QKeySequence)
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout,
							 QLabel, QFrame, QPushButton, QMessageBox,
							 QFileDialog, QScrollArea, QLineEdit,
							 QFormLayout, QGroupBox, QSizePolicy,
							 QTableWidget, QTableWidgetItem, QPlainTextEdit,
							 QShortcut, QMenu, qApp)

import app_constants
import misc
import gallerydb
import utils
import pewnet
import settings
import fetch

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical

class GalleryDownloaderUrlExtracter(QWidget):

	url_emit = pyqtSignal(str)

	def __init__(self, parent=None):
		super().__init__(parent, flags=Qt.Window|Qt.WindowStaysOnTopHint)
		self.main_layout = QVBoxLayout(self)
		self.text_area = QPlainTextEdit(self)
		self.text_area.setPlaceholderText("URLs are seperated by a newline")
		self.main_layout.addWidget(self.text_area)
		self.text_area.setWordWrapMode(QTextOption.NoWrap)
		add_to_queue = QPushButton('Add to queue')
		add_to_queue.adjustSize()
		add_to_queue.setFixedWidth(add_to_queue.width())
		add_to_queue.clicked.connect(self.add_to_queue)
		self.main_layout.addWidget(add_to_queue, 0, Qt.AlignRight)
		self.setWindowIcon(QIcon(app_constants.APP_ICO_PATH))
		self.show()

	def add_to_queue(self):
		txt = self.text_area.document().toPlainText()
		urls = txt.split('\n')
		for u in urls:
			if u:
				self.url_emit.emit(u)
		self.close()

class GalleryDownloaderItem(QObject):
	"""
	Receives a HenItem
	"""
	d_item_ready = pyqtSignal(object)
	def __init__(self, hitem):
		super().__init__()
		assert isinstance(hitem, pewnet.HenItem)
		self.d_item_ready.connect(self.done)
		self.item = hitem
		url = self.item.gallery_url

		self.profile_item = QTableWidgetItem(self.item.name)
		self.profile_item.setData(Qt.UserRole+1, hitem)
		self.profile_item.setToolTip(url)
		def set_profile(item):
			self.profile_item.setIcon(QIcon(item.thumb))
		self.item.thumb_rdy.connect(set_profile)

		# status
		self.status_item = QTableWidgetItem('In queue...')
		self.status_item.setToolTip(url)
		def set_finished(item):
			self.status_item.setText('Finished!')
			self.d_item_ready.emit(self)
		self.item.file_rdy.connect(set_finished)

		# other
		self.cost_item = QTableWidgetItem(self.item.cost)
		self.cost_item.setToolTip(url)
		self.size_item = QTableWidgetItem(self.item.size)
		self.size_item.setToolTip(url)
		type = 'Archive' if hitem.download_type == 0 else 'Torrent'
		self.type_item = QTableWidgetItem(type)
		self.type_item.setToolTip(url)

		self.status_timer = QTimer()
		self.status_timer.timeout.connect(self.check_progress)
		self.status_timer.start(500)

	def check_progress(self):
		if self.item.current_state == self.item.DOWNLOADING:
			btomb = 1048576
			self.status_item.setText("{0:.2f}/{1:.2f} MB".format(self.item.current_size/btomb,
															  self.item.total_size/btomb))
			self.size_item.setText("{0:.2f} MB".format(self.item.total_size/btomb))
		elif self.item.current_state == self.item.CANCELLED:
			self.status_item.setText("Cancelled!")
			self.status_timer.stop()

	def done(self):
		self.status_timer.stop()
		if self.item.download_type == 0:
			self.status_item.setText("Sent to library!")
		else:
			self.status_item.setText("Sent to torrent client!")

class GalleryDownloaderList(QTableWidget):
	"""
	"""
	init_fetch_instance = pyqtSignal(list)
	def __init__(self, gallery_model, parent):
		super().__init__(parent)
		self.gallery_model = gallery_model
		self.setColumnCount(5)
		self.setIconSize(QSize(50, 100))
		self.setAlternatingRowColors(True)
		self.setEditTriggers(self.NoEditTriggers)
		self.setFocusPolicy(Qt.NoFocus)
		v_header = self.verticalHeader()
		v_header.setSectionResizeMode(v_header.Fixed)
		v_header.setDefaultSectionSize(100)
		v_header.hide()
		self.setDragEnabled(False)
		self.setShowGrid(True)
		self.setSelectionBehavior(self.SelectRows)
		self.setSelectionMode(self.SingleSelection)
		self.setSortingEnabled(True)
		palette = self.palette()
		palette.setColor(palette.Highlight, QColor(88, 88, 88, 70))
		palette.setColor(palette.HighlightedText, QColor('black'))
		self.setPalette(palette)
		self.setHorizontalHeaderLabels(
			[' ', 'Status', 'Size', 'Cost', 'Type'])
		self.horizontalHeader().setStretchLastSection(True)
		self.horizontalHeader().setSectionResizeMode(0, self.horizontalHeader().Stretch)
		self.horizontalHeader().setSectionResizeMode(1, self.horizontalHeader().ResizeToContents)
		self.horizontalHeader().setSectionResizeMode(2, self.horizontalHeader().ResizeToContents)
		self.horizontalHeader().setSectionResizeMode(3, self.horizontalHeader().ResizeToContents)
		self.horizontalHeader().setSectionResizeMode(4, self.horizontalHeader().ResizeToContents)

		self.fetch_instance = fetch.Fetch()
		self.fetch_instance.download_items = []
		self.fetch_instance.FINISHED.connect(self._gallery_to_model)
		self.fetch_instance.moveToThread(app_constants.GENERAL_THREAD)
		self.init_fetch_instance.connect(self.fetch_instance.local)

		def open_item(idx):
			hitem = self._get_hitem(idx)
			if hitem.current_state == hitem.DOWNLOADING:
				hitem.open(True)
		self.doubleClicked.connect(open_item)

	def add_entry(self, hitem):
		assert isinstance(hitem, pewnet.HenItem)
		g_item = GalleryDownloaderItem(hitem)
		if hitem.download_type == 0:
			g_item.d_item_ready.connect(self._init_gallery)

		self.insertRow(0)
		self.setSortingEnabled(False)
		self.setItem(0, 0, g_item.profile_item)
		self.setItem(0, 1, g_item.status_item)
		self.setItem(0, 2, g_item.size_item)
		self.setItem(0, 3, g_item.cost_item)
		self.setItem(0, 4, g_item.type_item)
		self.setSortingEnabled(True)

	def _get_hitem(self, idx):
		r = idx.row()
		return self.item(r, 0).data(Qt.UserRole+1)

	def contextMenuEvent(self, event):
		idx = self.indexAt(event.pos())
		if idx.isValid():
			hitem = self._get_hitem(idx)
			clipboard = qApp.clipboard()
			menu = QMenu()
			if hitem.current_state == hitem.DOWNLOADING:
				menu.addAction("Cancel", hitem.cancel)
			if hitem.current_state == hitem.FINISHED:
				menu.addAction("Open", hitem.open)
				menu.addAction("Show in folder", lambda: hitem.open(True))
			menu.addAction("Copy path", lambda: clipboard.setText(hitem.file))
			menu.addAction("Copy gallery URL", lambda: clipboard.setText(hitem.gallery_url))
			menu.addAction("Copy download URL", lambda: clipboard.setText(hitem.download_url))
			if not hitem.current_state == hitem.DOWNLOADING:
				menu.addAction("Remove", lambda: self.removeRow(idx.row()))
			menu.exec_(event.globalPos())
			event.accept()
			del menu
		else:
			event.ignore()

	def _init_gallery(self, download_item):
		assert isinstance(download_item, GalleryDownloaderItem)
		app_constants.TEMP_PATH_IGNORE.append(os.path.normcase(download_item.item.file))
		self.fetch_instance.download_items.append(download_item)
		self.init_fetch_instance.emit([download_item.item.file])

	def _gallery_to_model(self, gallery_list):
		log_i("Adding downloaded gallery to library")
		try:
			d_item = self.fetch_instance.download_items.pop(0)
		except IndexError:
			return
		if gallery_list:
			gallery = gallery_list[0]
			gallery.link = d_item.item.gallery_url
			if d_item.item.metadata:
				gallery = pewnet.EHen.apply_metadata(gallery, d_item.item.metadata)
			gallerydb.add_method_queue(
				gallerydb.GalleryDB.add_gallery_return, False, gallery)
			self.gallery_model.insertRows([gallery], None, 1)
			self.gallery_model.init_search(self.gallery_model.current_term)
			d_item.status_item.setText('Added to library!')
			log_i("Added downloaded gallery to library")
		else:
			d_item.status_item.setText('Adding to library failed!')
			log_i("Could not add downloaded gallery to library")

	def clear_list(self):
		for r in range(self.rowCount()-1, -1, -1):
			status = self.item(r, 1)
			if '!' in status.text():
				self.removeRow(r)

class GalleryDownloader(QWidget):
	"""
	A gallery downloader window
	"""
	def __init__(self, parent):
		super().__init__(None,
				   Qt.CustomizeWindowHint | Qt.WindowTitleHint | Qt.WindowMinMaxButtonsHint)
		self.setAttribute(Qt.WA_DeleteOnClose)
		main_layout = QVBoxLayout(self)
		self.parent_widget = parent
		self.url_inserter = QLineEdit()
		self.url_inserter.setPlaceholderText("Hover to see supported URLs")
		self.url_inserter.setToolTip(app_constants.SUPPORTED_DOWNLOAD_URLS)
		self.url_inserter.setToolTipDuration(999999999)
		self.url_inserter.returnPressed.connect(self.add_download_entry)
		main_layout.addWidget(self.url_inserter)
		self.info_lbl = QLabel(self)
		self.info_lbl.setAlignment(Qt.AlignCenter)
		main_layout.addWidget(self.info_lbl)
		self.info_lbl.hide()
		buttons_layout = QHBoxLayout()
		url_window_btn = QPushButton('Batch URLs')
		url_window_btn.adjustSize()
		url_window_btn.setFixedWidth(url_window_btn.width())
		def batch_url_win():
			self._batch_url = GalleryDownloaderUrlExtracter()
			self._batch_url.url_emit.connect(self.add_download_entry)
		url_window_btn.clicked.connect(batch_url_win)
		clear_all_btn = QPushButton('Clear List')
		clear_all_btn.adjustSize()
		clear_all_btn.setFixedWidth(clear_all_btn.width())
		buttons_layout.addWidget(url_window_btn, 0, Qt.AlignLeft)
		buttons_layout.addWidget(clear_all_btn, 0, Qt.AlignRight)
		main_layout.addLayout(buttons_layout)
		self.download_list = GalleryDownloaderList(parent.manga_list_view.sort_model, self)
		clear_all_btn.clicked.connect(self.download_list.clear_list)
		download_list_scroll = QScrollArea(self)
		download_list_scroll.setBackgroundRole(self.palette().Base)
		download_list_scroll.setWidgetResizable(True)
		download_list_scroll.setWidget(self.download_list)
		main_layout.addWidget(download_list_scroll, 1)
		close_button = QPushButton('Close', self)
		close_button.clicked.connect(self.hide)
		main_layout.addWidget(close_button)
		self.resize(480,600)
		self.setWindowIcon(QIcon(app_constants.APP_ICO_PATH))

	def add_download_entry(self, url=None):
		log_i('Adding download entry: {}'.format(url))
		self.info_lbl.hide()
		h_item = None
		try:
			if not url:
				url = self.url_inserter.text()
				if not url:
					return
				self.url_inserter.clear()
			url = url.lower()
			
			manager = self.website_validator(url)
			h_item = manager.from_gallery_url(url)
		except app_constants.WrongURL:
			self.info_lbl.setText("<font color='red'>Failed to add:\n{}</font>".format(url))
			self.info_lbl.show()
			return
		except app_constants.NeedLogin:
			self.info_lbl.setText("<font color='red'>Login is required to download:\n{}</font>".format(url))
			self.info_lbl.show()
			return
		except app_constants.WrongLogin:
			self.info_lbl.setText("<font color='red'Wrong login info to download:\n{}</font>".format(url))
			self.info_lbl.show()
			return
		if h_item:
			log_i('Successfully added download entry')
			self.download_list.add_entry(h_item)

	def website_validator(self, url):
		match_prefix = "^(http\:\/\/|https\:\/\/)?(www\.)?([^\.]?)" # http:// or https:// + www.
		match_base = "(.*\.)+" # base. Replace with domain
		match_tld = "[a-zA-Z0-9][a-zA-Z0-9\-]*" # com
		end = "/?$"

		# ATTENTION: the prefix will automatically get prepended to the pattern string! Don't try to match it.

		def regex_validate(r):
			if re.fullmatch(match_prefix+r+end, url):
				return True
			return False

		if regex_validate("((g\.e-hentai)\.org\/g\/[0-9]+\/[a-z0-9]+)"):
			manager = pewnet.HenManager()
		elif regex_validate("((exhentai)\.org\/g\/[0-9]+\/[a-z0-9]+)"):
			exprops = settings.ExProperties()
			if exprops.check():
				manager = pewnet.ExHenManager()
			else:
				return
		elif regex_validate("(panda\.chaika\.moe\/(archive|gallery)\/[0-9]+)"):
			manager = pewnet.ChaikaManager()
		else:
			raise app_constants.WrongURL

		return manager

	def show(self):
		if self.isVisible():
			self.activateWindow()
		else:
			super().show()

class GalleryPopup(misc.BasePopup):
	"""
	Pass a tuple with text and a list of galleries
	gallery profiles won't be scaled if scale is set to false
	"""
	gallery_doubleclicked = pyqtSignal(gallerydb.Gallery)
	def __init__(self, tup_gallery, parent = None, menu = None):
		super().__init__(parent)
		self.setMaximumWidth(16777215)
		assert isinstance(tup_gallery, tuple), "Incorrect type received, expected tuple"
		assert isinstance(tup_gallery[0], str) and isinstance(tup_gallery[1], list)
		main_layout = QVBoxLayout()
		# todo make it scroll
		scroll_area = QScrollArea()
		dummy = QWidget()
		self.gallery_layout = misc.FlowLayout(dummy)
		scroll_area.setWidgetResizable(True)
		scroll_area.setMaximumHeight(400)
		scroll_area.setMidLineWidth(620)
		scroll_area.setBackgroundRole(scroll_area.palette().Shadow)
		scroll_area.setFrameStyle(scroll_area.NoFrame)
		scroll_area.setWidget(dummy)
		text = tup_gallery[0]
		galleries = tup_gallery[1]
		main_layout.addWidget(scroll_area, 3)
		for g in galleries:
			gall_w = misc.GalleryShowcaseWidget(parent=self, menu=menu())
			gall_w.set_gallery(g, (170//1.40, 170))
			gall_w.double_clicked.connect(self.gallery_doubleclicked.emit)
			self.gallery_layout.addWidget(gall_w)

		text_lbl =  QLabel(text)
		text_lbl.setAlignment(Qt.AlignCenter)
		main_layout.addWidget(text_lbl)
		main_layout.addLayout(self.buttons_layout)
		self.main_widget.setLayout(main_layout)
		self.setMaximumHeight(500)
		self.setMaximumWidth(620)
		self.resize(620, 500)
		self.show()

	def get_all_items(self):
		n = self.gallery_layout.rowCount()
		items = []
		for x in range(n):
			item = self.gallery_layout.itemAt(x)
			items.append(item.widget())
		return items

class ModifiedPopup(misc.BasePopup):
	def __init__(self, path, gallery_id, parent=None):
		super().__init__(parent)
		main_layout = QVBoxLayout()
		main_layout.addWidget(QLabel("Modified:\npath: {}\nID:{}".format(path, gallery_id)))
		self.main_widget.setLayout(main_layout)
		self.show()

class CreatedPopup(misc.BasePopup):
	ADD_SIGNAL = pyqtSignal(str)
	def __init__(self, path, parent=None):
		super().__init__(parent)
		def commit():
			self.ADD_SIGNAL.emit(path)
			self.close()
		main_layout = QVBoxLayout()
		inner_layout = QHBoxLayout()
		name = os.path.split(path)[1]
		cover = QLabel()
		img = QPixmap(utils.get_gallery_img(path))
		if img:
			cover.setPixmap(img.scaled(350, 200, Qt.KeepAspectRatio, Qt.SmoothTransformation))
		info_lbl = QLabel('New gallery detected!\n\n{}\n\nDo you want to add it?'.format(name))
		info_lbl.setWordWrap(True)
		info_lbl.setAlignment(Qt.AlignCenter)
		inner_layout.addWidget(cover)
		inner_layout.addWidget(info_lbl)
		main_layout.addLayout(inner_layout)
		main_layout.addLayout(self.generic_buttons)
		self.main_widget.setLayout(main_layout)
		self.yes_button.clicked.connect(commit)
		self.no_button.clicked.connect(self.close)
		self.adjustSize()
		self.show()

class MovedPopup(misc.BasePopup):
	UPDATE_SIGNAL = pyqtSignal(object)
	def __init__(self, new_path, gallery, parent=None):
		super().__init__(parent)
		def commit():
			g = utils.update_gallery_path(new_path, gallery)
			self.UPDATE_SIGNAL.emit(g)
			self.close()
		def cancel():
			gallery.dead_link = True
			self.close()
		main_layout = QVBoxLayout()
		inner_layout = QHBoxLayout()
		title = QLabel(gallery.title)
		title.setWordWrap(True)
		title.setAlignment(Qt.AlignCenter)
		title.adjustSize()
		cover = QLabel()
		img = QPixmap(gallery.profile)
		cover.setPixmap(img)
		text = QLabel("The path to this gallery has been renamed\n"+
				"\n{}\n".format(os.path.basename(gallery.path))+u'\u2192'+"\n{}".format(os.path.basename(new_path)))
		
		text.setWordWrap(True)
		text.setAlignment(Qt.AlignCenter)
		button_layout = QHBoxLayout()
		update_btn = QPushButton('Update')
		update_btn.clicked.connect(commit)
		close_btn = QPushButton('Close')
		close_btn.clicked.connect(cancel)
		button_layout.addWidget(update_btn)
		button_layout.addWidget(close_btn)

		inner_layout.addWidget(cover)
		inner_layout.addWidget(text)
		main_layout.addWidget(title)
		main_layout.addLayout(inner_layout)
		main_layout.addLayout(button_layout)
		self.main_widget.setLayout(main_layout)

		self.show()

class DeletedPopup(misc.BasePopup):
	REMOVE_SIGNAL = pyqtSignal(object)
	UPDATE_SIGNAL = pyqtSignal(object)
	def __init__(self, path, gallery, parent=None):
		super().__init__(parent)
		gallery.dead_link = True
		def commit():
			msgbox = QMessageBox(self)
			msgbox.setIcon(QMessageBox.Question)
			msgbox.setWindowTitle('Type of gallery source')
			msgbox.setInformativeText('What type of gallery source is it?')
			dir = msgbox.addButton('Directory', QMessageBox.YesRole)
			archive = msgbox.addButton('Archive', QMessageBox.NoRole)
			msgbox.exec()
			new_path = ''
			if msgbox.clickedButton() == dir:
				new_path = QFileDialog.getExistingDirectory(self, 'Choose directory')
			elif msgbox.clickedButton() == archive:
				new_path = QFileDialog.getOpenFileName(self, 'Choose archive',
										   filter=utils.FILE_FILTER)
				new_path = new_path[0]
			else: return None
			if new_path:
				g = utils.update_gallery_path(new_path, gallery)
				self.UPDATE_SIGNAL.emit(g)
				self.close()

		def remove_commit():
			self.REMOVE_SIGNAL.emit(gallery)
			self.close()

		main_layout = QVBoxLayout()
		inner_layout = QHBoxLayout()
		cover = QLabel()
		img = QPixmap(gallery.profile)
		cover.setPixmap(img)
		title_lbl = QLabel(gallery.title)
		title_lbl.setAlignment(Qt.AlignCenter)
		info_lbl = QLabel("The path to this gallery has been removed\n"+
					"What do you want to do?")
		#info_lbl.setWordWrap(True)
		path_lbl = QLabel(path)
		path_lbl.setWordWrap(True)
		info_lbl.setAlignment(Qt.AlignCenter)
		inner_layout.addWidget(cover)
		inner_layout.addWidget(info_lbl)
		main_layout.addLayout(inner_layout)
		main_layout.addWidget(path_lbl)
		close_btn = QPushButton('Close')
		close_btn.clicked.connect(self.close)
		update_btn = QPushButton('Update path...')
		update_btn.clicked.connect(commit)
		remove_btn = QPushButton('Remove')
		remove_btn.clicked.connect(remove_commit)
		buttons_layout = QHBoxLayout()
		buttons_layout.addWidget(remove_btn)
		buttons_layout.addWidget(update_btn)
		buttons_layout.addWidget(close_btn)
		main_layout.addWidget(title_lbl)
		main_layout.addLayout(buttons_layout)
		self.main_widget.setLayout(main_layout)
		self.adjustSize()
		self.show()

class GalleryHandler(FileSystemEventHandler, QObject):
	CREATE_SIGNAL = pyqtSignal(str)
	MODIFIED_SIGNAL = pyqtSignal(str, int)
	DELETED_SIGNAL = pyqtSignal(str, object)
	MOVED_SIGNAL = pyqtSignal(str, object)

	def __init__(self):
		super().__init__()
		#self.g_queue = []

	def file_filter(self, event):
		if os.path.normcase(event.src_path) in app_constants.TEMP_PATH_IGNORE:
			app_constants.TEMP_PATH_IGNORE.remove(os.path.normcase(event.src_path))
			return False
		# TODO: use utils.check_ignore_list?
		_, ext = os.path.splitext(event.src_path)
		if event.is_directory or ext in utils.ARCHIVE_FILES:
			if event.is_directory and "Folder" in app_constants.IGNORE_EXTS:
				return False
			if ext[1:].upper() in app_constants.IGNORE_EXTS:
				return False
			return True
		return False

	#def process_queue(self, type):
	#	if self.g_queue:
	#		if type == 'create':
	#			self.CREATE_SIGNAL.emit(self.g_queue)

	#	self.g_queue = []

	def on_created(self, event):
		if not app_constants.OVERRIDE_MONITOR:
			if self.file_filter(event):
				t = Timer(8, self.CREATE_SIGNAL.emit, args=(event.src_path,))
				t.start()
		else:
			app_constants.OVERRIDE_MONITOR = False

	def on_deleted(self, event):
		if not app_constants.OVERRIDE_MONITOR:
			path = event.src_path
			gallery = gallerydb.GalleryDB.get_gallery_by_path(path)
			if gallery:
				self.DELETED_SIGNAL.emit(path, gallery)
		else:
			app_constants.OVERRIDE_MONITOR = False

	def on_modified(self, event):
		pass

	def on_moved(self, event):
		if not app_constants.OVERRIDE_MONITOR:
			if self.file_filter(event):
				old_path = event.src_path
				gallery = gallerydb.GalleryDB.get_gallery_by_path(old_path)
				if gallery:
					self.MOVED_SIGNAL.emit(event.dest_path, gallery)
		else:
			app_constants.OVERRIDE_MONITOR = False

class Watchers:
	def __init__(self):

		self.gallery_handler = GalleryHandler()
		self.watchers = []
		for path in app_constants.MONITOR_PATHS:
			gallery_observer = Observer()

			try:
				gallery_observer.schedule(self.gallery_handler, path, True)
				gallery_observer.start()
				self.watchers.append(gallery_observer)
			except:
				log.exception('Could not monitor: {}'.format(path.encode(errors='ignore')))
	
	def stop_all(self):
		for watcher in self.watchers:
			watcher.stop()

class ImpExpData:

	def __init__(self, format=1):
		self.type = format
		if format == 0:
			self.structure = ""
		else:
			self.structure = {}
		self.hash_pages_count = 4

	def get_pages(self, pages):
		"Returns pages to generate hashes from"
		p = []
		if pages < self.hash_pages_count+1:
			for x in range(pages):
				p.append(x)
		else:
			x = 0
			i = pages//self.hash_pages_count
			for t in range(self.hash_pages_count):
				x += i
				p.append(x-1)
		return p

	def add_data(self, name, data):
		if self.type == 0:
			pass
		else:
			self.structure[name] = data

	def save(self, file_path):
		file_name = os.path.join(file_path,
						   'happypanda-{}.hpdb'.format(
							  datetime.datetime.now().strftime("%Y-%m-%d %H-%M-%S")))
		with open(file_name, 'w', encoding='utf-8') as fp:
			json.dump(self.structure, fp, indent=4)

	def find_pair(self, found_pairs):
		identifier = self.structure['identifier']
		found = None
		for g in app_constants.GALLERY_DATA:
			if not g in found_pairs and g.chapters[0].pages == identifier['pages']:
				pages = self.get_pages(g.chapters[0].pages)
				hashes = gallerydb.HashDB.gen_gallery_hash(g, 0, pages)
				for p in hashes:
					if hashes[p] != identifier[str(p)]:
						break
				else:
					found = g
					g.title = self.structure['title']
					g.artist = self.structure['artist']
					if self.structure['pub_date'] and self.structure['pub_date'] != 'None':
						g.pub_date = datetime.datetime.strptime(
							self.structure['pub_date'], "%Y-%m-%d %H:%M:%S")
					g.type = self.structure['type']
					g.status = self.structure['status']
					if self.structure['last_read'] and self.structure['last_read'] != 'None':
						g.last_read = datetime.datetime.strptime(
							self.structure['last_read'], "%Y-%m-%d %H:%M:%S")
					g.times_read += self.structure['times_read']
					g._db_v = self.structure['db_v']
					g.language = self.structure['language']
					g.link = self.structure['link']
					for ns in self.structure['tags']:
						if not ns in g.tags:
							g.tags[ns] = []
						for tag in self.structure['tags'][ns]:
							if not tag in g.tags[ns]:
								g.tags[ns].append(tag)
					g.exed = self.structure['exed']
					g.info = self.structure['info']
					g.fav = self.structure['fav']
					gallerydb.GalleryDB.modify_gallery(
						g.id,
						g.title,
						artist=g.artist,
						info=g.info,
						type=g.type,
						fav=g.fav,
						tags=g.tags,
						language=g.language,
						status=g.status,
						pub_date=g.pub_date,
						link=g.link,
						times_read=g.times_read,
						_db_v=g._db_v,
						exed=g.exed
						)

			if found:
				break

		return found

class ImportExport(QObject):
	finished = pyqtSignal()
	imported_g = pyqtSignal(str)
	progress = pyqtSignal(int)
	amount = pyqtSignal(int)

	def __init__(self):
		super().__init__()
	
	def import_data(self, path):
		with open(path, 'r', encoding='utf-8') as fp:
			data = json.load(fp)
			data_count = len(data)
			self.amount.emit(data_count)
			pairs_found = []
			for prog, g_id in enumerate(data, 1):
				g_data = ImpExpData()
				g_data.structure.update(data[g_id])
				g = g_data.find_pair(pairs_found)
				if g:
					pairs_found.append(g)
				self.imported_g.emit(
					"Importing database file... ({}/{} imported)".format(len(pairs_found), data_count))
				self.progress.emit(prog)
			self.finished.emit()

	def export_data(self, gallery=None):
		galleries = []
		if gallery:
			galleries.append(gallery)
		else:
			galleries = app_constants.GALLERY_DATA

		amount = len(galleries)
		log_i("Exporting {} galleries".format(amount))
		data = ImpExpData(app_constants.EXPORT_FORMAT)
		self.amount.emit(amount)
		for prog, g in enumerate(galleries, 1):
			log_d("Exporting {} out of {} galleries".format(prog, amount))
			g_data = {}
			g_data['title'] = g.title
			g_data['artist'] = g.artist
			g_data['info'] = g.info
			g_data['fav'] = g.fav
			g_data['type'] = g.type
			g_data['link'] = g.link
			g_data['language'] = g.language
			g_data['status'] = g.status
			g_data['pub_date'] = "{}".format(g.pub_date)
			g_data['last_read'] = "{}".format(g.last_read)
			g_data['times_read'] = g.times_read
			g_data['exed'] = g.exed
			g_data['db_v'] = g._db_v
			g_data['tags'] = g.tags.copy()
			g_data['identifier'] = {'pages':g.chapters[0].pages}
			pages = data.get_pages(g.chapters[0].pages)
			try:
				h_list = gallerydb.HashDB.gen_gallery_hash(g, 0, pages)
			except app_constants.InternalPagesMismatch:
				if g.chapters.update_chapter_pages(0):
					pages = data.get_pages(g.chapters[0].pages)
					h_list = gallerydb.HashDB.gen_gallery_hash(g, 0, pages)
				else:
					h_list = {}
			if not h_list:
				log_e("Failed to export gallery: {}".format(g.title.encode(errors='ignore')))
				continue
			for n in pages:
				g_data['identifier'][n] = h_list[n]

			data.add_data(str(g.id), g_data)
			self.progress.emit(prog)

		log_i("Finished exporting galleries!")
		data.save(app_constants.EXPORT_PATH)
		self.finished.emit()

