import logging, os
from watchdog.events import FileSystemEventHandler, DirDeletedEvent
from watchdog.observers import Observer
from threading import Timer

from PyQt5.QtCore import Qt, QObject, pyqtSignal, QTimer, QSize
from PyQt5.QtGui import QPixmap, QIcon, QColor
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout,
							 QLabel, QFrame, QPushButton, QMessageBox,
							 QFileDialog, QScrollArea, QLineEdit,
							 QFormLayout, QGroupBox, QSizePolicy,
							 QTableWidget, QTableWidgetItem)

import gui_constants
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

class GalleryDownloaderItem(QObject):
	"""
	Receives a HenItem
	"""
	d_item_ready = pyqtSignal(object)
	def __init__(self, hitem):
		super().__init__()
		assert isinstance(hitem, pewnet.HenItem)
		self.item = hitem
		url = self.item.gallery_url

		self.profile_item = QTableWidgetItem(self.item.name)
		self.profile_item.setToolTip(url)
		def set_profile(item):
			self.profile_item.setIcon(QIcon(item.thumb))
		self.item.thumb_rdy.connect(set_profile)

		# status
		self.status_item = QTableWidgetItem('Downloading...')
		self.status_item.setToolTip(url)
		def set_finished(item):
			self.status_item.setText('Finished downloading!')
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
		self.horizontalHeader().setStretchLastSection(True)
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

		self.fetch_instance = fetch.Fetch()
		self.fetch_instance.download_items = []
		self.fetch_instance.FINISHED.connect(self.gallery_to_model)
		self.fetch_instance.moveToThread(gui_constants.GENERAL_THREAD)
		self.init_fetch_instance.connect(self.fetch_instance.local)

	def add_entry(self, hitem):
		assert isinstance(hitem, pewnet.HenItem)
		g_item = GalleryDownloaderItem(hitem)
		if hitem.download_type == 0:
			g_item.d_item_ready.connect(self.init_gallery)
		elif hitem.download_type == 1:
			g_item.d_item_ready.connect(lambda: g_item.status_item.setText('Sent to torrent client!'))

		self.insertRow(0)
		self.setSortingEnabled(False)
		self.setItem(0, 0, g_item.profile_item)
		self.setItem(0, 1, g_item.status_item)
		self.setItem(0, 2, g_item.size_item)
		self.setItem(0, 3, g_item.cost_item)
		self.setItem(0, 4, g_item.type_item)
		self.setSortingEnabled(True)

	def init_gallery(self, download_item):
		assert isinstance(download_item, GalleryDownloaderItem)
		download_item.status_item.setText('Adding to library...')
		self.fetch_instance.download_items.append(download_item)
		self.init_fetch_instance.emit([download_item.item.file])

	def gallery_to_model(self, gallery_list):
		try:
			d_item = self.fetch_instance.download_items.pop(0)
		except IndexError:
			return
		if gallery_list:
			gallery = gallery_list[0]
			if d_item.item.metadata:
				gallery = fetch.Fetch.apply_metadata(gallery, d_item.item.metadata)
			gallery.link = d_item.item.gallery_url
			gallerydb.add_method_queue(
				gallerydb.GalleryDB.add_gallery_return, False, gallery)
			self.gallery_model.insertRows([gallery], None, 1)
			self.gallery_model.init_search(self.gallery_model.current_term)
			d_item.status_item.setText('Added to library!')
		else:
			d_item.status_item.setText('Adding to library failed!')

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
		self.url_inserter.setToolTip(gui_constants.SUPPORTED_DOWNLOAD_URLS)
		self.url_inserter.setToolTipDuration(999999999)
		self.url_inserter.returnPressed.connect(self.add_download_entry)
		main_layout.addWidget(self.url_inserter)
		self.info_lbl = QLabel(self)
		self.info_lbl.setAlignment(Qt.AlignCenter)
		main_layout.addWidget(self.info_lbl)
		self.info_lbl.hide()
		buttons_layout = QHBoxLayout()
		clear_all_btn = QPushButton('Clear List')
		clear_all_btn.adjustSize()
		clear_all_btn.setFixedWidth(clear_all_btn.width())
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
		self.setWindowIcon(QIcon(gui_constants.APP_ICO_PATH))

	def add_download_entry(self, url=None):
		self.info_lbl.hide()
		h_item = None
		try:
			if not url:
				url = self.url_inserter.text().lower()
				if not url:
					return
				self.url_inserter.clear()
			if 'g.e-hentai.org' in url:
				manager = pewnet.HenManager()
			elif 'exhentai.org' in url:
				exprops = settings.ExProperties()
				if exprops.check():
					manager = pewnet.ExHenManager(exprops.ipb_id, exprops.ipb_pass)
				else:
					return
			elif 'panda.chaika.moe' in url and ('/archive/' in url or '/gallery/' in url):
				manager = pewnet.ChaikaManager()
			else:
				raise pewnet.WrongURL

			h_item = manager.from_gallery_url(url)
		except pewnet.WrongURL:
			self.info_lbl.setText("<font color='red'>Failed to add to download list</font>")
			self.info_lbl.show()
			return
		if h_item:
			self.download_list.add_entry(h_item)

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
			gall_w = misc.GalleryShowcaseWidget(parent=self, menu=menu)
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

	#def get_all_items(self):
	#	n = self.gallery_layout.rowCount()
	#	items = []
	#	for x in range(n):
	#		item = self.gallery_layout.itemAt(x)
	#		items.append(item.widget())
	#	return items

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
				"\n{}\n".format(gallery.path)+u'\u2192'+"\n{}".format(new_path))
		text.setWordWrap(True)
		text.setAlignment(Qt.AlignCenter)
		button_layout = QHBoxLayout()
		update_btn = QPushButton('Update')
		update_btn.clicked.connect(commit)
		close_btn = QPushButton('Close')
		close_btn.clicked.connect(self.close)
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
		name = os.path.split(event.src_path)[1]
		if event.is_directory or name.endswith(tuple(utils.ARCHIVE_FILES)):
			return True
		else: return False

	#def process_queue(self, type):
	#	if self.g_queue:
	#		if type == 'create':
	#			self.CREATE_SIGNAL.emit(self.g_queue)

	#	self.g_queue = []

	def on_created(self, event):
		if not gui_constants.OVERRIDE_MONITOR:
			if self.file_filter(event):
				t = Timer(8, self.CREATE_SIGNAL.emit, args=(event.src_path,))
				t.start()
		else:
			gui_constants.OVERRIDE_MONITOR = False

	def on_deleted(self, event):
		if not gui_constants.OVERRIDE_MONITOR:
			path = event.src_path
			gallery = gallerydb.GalleryDB.get_gallery_by_path(path)
			if gallery:
				self.DELETED_SIGNAL.emit(path, gallery)
		else:
			gui_constants.OVERRIDE_MONITOR = False

	def on_modified(self, event):
		pass

	def on_moved(self, event):
		if not gui_constants.OVERRIDE_MONITOR:
			if self.file_filter(event):
				old_path = event.src_path
				gallery = gallerydb.GalleryDB.get_gallery_by_path(old_path)
				if gallery:
					self.MOVED_SIGNAL.emit(event.dest_path, gallery)
		else:
			gui_constants.OVERRIDE_MONITOR = False

class Watchers:
	def __init__(self):

		self.gallery_handler = GalleryHandler()
		self.watchers = []
		for path in gui_constants.MONITOR_PATHS:
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
