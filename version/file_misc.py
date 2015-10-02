import logging, os
from watchdog.events import FileSystemEventHandler, DirDeletedEvent
from watchdog.observers import Observer
from threading import Timer

from PyQt5.QtCore import Qt, QObject, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout,
							 QLabel, QFrame, QPushButton, QMessageBox,
							 QFileDialog, QScrollArea, QLineEdit,
							 QFormLayout, QGroupBox, QSizePolicy)

import gui_constants
import misc
import gallerydb
import utils
import pewnet
import settings

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical

class GalleryDownloaderItem(QWidget):
	"""
	"""
	def __init__(self, hitem, parent=None):
		assert isinstance(hitem, pewnet.HenItem)
		super().__init__(parent)
		self.setFixedHeight(50)
		self.setContentsMargins(0,0,0,0)
		self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
		self.setBackgroundRole(self.palette().Dark)
		l = QHBoxLayout(self)
		l.setContentsMargins(0,0,0,0)
		self.item = hitem

		separators = []
		for s in range(2):
			sep = QFrame()
			sep.setFrameStyle(QFrame.VLine)
			sep.setFrameShadow(QFrame.Sunken)
			separators.append(sep)
		
		#thumb
		self.profile = QLabel()
		l.addWidget(self.profile)
		l.addWidget(separators[0])

		def set_profile(item):
			self.profile.setPixmap(QPixmap(item.thumb).scaled(
				50, 25, Qt.KeepAspectRatio, Qt.SmoothTransformation))
		self.item.thumb_rdy.connect(set_profile)

		# status
		self.status_text = QLabel('Status:\nDownloading...')
		def set_finished(item):
			self.status_text.setText('Status:\nDone!')
		self.item.file_rdy.connect(set_finished)

		l.addWidget(self.status_text)
		l.addWidget(separators[1])

		# url 
		v_l = QVBoxLayout()
		title_lbl = QLabel(self.item.metadata['title']['def'])
		small_h_l = QHBoxLayout()
		cost_lbl = QLabel("Cost: {}".format(self.item.cost))
		size_lbl = QLabel("Size: {}".format(self.item.size))
		small_h_l.addWidget(cost_lbl)
		small_h_l.addWidget(size_lbl, 1)
		url_lbl = QLabel(self.item.gallery_url)
		v_l.addWidget(title_lbl)
		v_l.addLayout(small_h_l)
		v_l.addWidget(url_lbl)
		l.addLayout(v_l, 1)


class GalleryDownloaderList(QGroupBox):
	"""
	"""
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setTitle('Download list')
		self.main_layout = QFormLayout(self)

	def add_entry(self, hitem):
		assert isinstance(hitem, pewnet.HenItem)
		item_widget = GalleryDownloaderItem(hitem)
		self.main_layout.addRow(item_widget)


class GalleryDownloader(QWidget):
	"""
	A gallery downloader window
	"""
	def __init__(self, parent=None):
		super().__init__(parent, Qt.Window)
		self.setAttribute(Qt.WA_DeleteOnClose)
		main_layout = QVBoxLayout(self)
		self.url_inserter = QLineEdit()
		self.url_inserter.setPlaceholderText("Hover to see supported URLs")
		self.url_inserter.setToolTip("Supported URLs:\nExhentai/g.e-hentai gallery links, e.g.:"+
							   " http://g.e-hentai.org/g/618395/0439fa3666/")
		self.url_inserter.returnPressed.connect(self.add_download_entry)
		main_layout.addWidget(self.url_inserter)

		self.download_list = GalleryDownloaderList(self)
		download_list_scroll = QScrollArea(self)
		download_list_scroll.setBackgroundRole(self.palette().Base)
		download_list_scroll.setWidgetResizable(True)
		download_list_scroll.setWidget(self.download_list)
		main_layout.addWidget(download_list_scroll, 1)
		self.resize(600,600)

	def add_download_entry(self, url=None):
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
		h_item = manager.from_gallery_url(url)
		if h_item:
			self.download_list.add_entry(h_item)

	def closeEvent(self, event):
		self.hide()

class GalleryPopup(misc.BasePopup):
	"""
	Pass a tuple with text and a list of galleries
	gallery profiles won't be scaled if scale is set to false
	"""

	def __init__(self, tup_gallery, parent = None):
		super().__init__(parent)
		self.setMaximumWidth(16777215)
		assert isinstance(tup_gallery, tuple), "Incorrect type received, expected tuple"
		assert isinstance(tup_gallery[0], str) and isinstance(tup_gallery[1], list)
		main_layout = QVBoxLayout()
		# todo make it scroll
		scroll_area = QScrollArea()
		dummy = QWidget()
		gallery_layout = misc.FlowLayout(dummy)
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
			gall_w = misc.GalleryShowcaseWidget(parent=self)
			gall_w.set_gallery(g, (170//1.40, 170))
			gallery_layout.addWidget(gall_w)

		text_lbl =  QLabel(text)
		text_lbl.setAlignment(Qt.AlignCenter)
		main_layout.addWidget(text_lbl)
		main_layout.addLayout(self.buttons_layout)
		self.main_widget.setLayout(main_layout)
		self.setMaximumHeight(500)
		self.setMaximumWidth(620)
		self.resize(620, 500)
		self.show()

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
			msgbox.setWindowTitle('Type of file')
			msgbox.setInformativeText('What type of file is it?')
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
