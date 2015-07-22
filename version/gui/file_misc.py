import logging, os
from PyQt5.QtCore import Qt, QObject, pyqtSignal, QTimer
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout,
							 QLabel, QFrame, QPushButton, QMessageBox,
							 QFileDialog, QScrollArea)
from watchdog.events import FileSystemEventHandler, DirDeletedEvent
from watchdog.observers import Observer
from threading import Timer
from . import gui_constants, misc
from .misc import BasePopup
from ..database import gallerydb
from .. import utils

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical

def update_gallery_path(new_path, gallery):
	"Updates a gallery's & it's chapters' path"
	for chap_numb in gallery.chapters:
		chap_path = gallery.chapters[chap_numb]
		head, tail = os.path.split(chap_path)
		if gallery.path == chap_path:
			chap_path = new_path
		elif gallery.path == head:
			chap_path = os.path.join(new_path, tail)

		gallery.chapters[chap_numb] = chap_path

	gallery.path = new_path
	return gallery

class GalleryPopup(BasePopup):
	"""
	Pass a tuple with text and a list of galleries
	"""

	def __init__(self, tup_gallery, parent = None,):
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

class ModifiedPopup(BasePopup):
	def __init__(self, path, gallery_id, parent=None):
		super().__init__(parent)
		main_layout = QVBoxLayout()
		main_layout.addWidget(QLabel("Modified:\npath: {}\nID:{}".format(path, gallery_id)))
		self.main_widget.setLayout(main_layout)
		self.show()

class CreatedPopup(BasePopup):
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

class MovedPopup(BasePopup):
	UPDATE_SIGNAL = pyqtSignal(object)
	def __init__(self, new_path, gallery, parent=None):
		super().__init__(parent)
		def commit():
			g = update_gallery_path(new_path, gallery)
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

class DeletedPopup(BasePopup):
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
				g = update_gallery_path(new_path, gallery)
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
		if self.file_filter(event):
			t = Timer(8, self.CREATE_SIGNAL.emit, args=(event.src_path,))
			t.start()

	def on_deleted(self, event):
		path = event.src_path
		gallery = gallerydb.GalleryDB.get_gallery_by_path(path)
		if gallery:
			self.DELETED_SIGNAL.emit(path, gallery)

	def on_modified(self, event):
		pass

	def on_moved(self, event):
		if self.file_filter(event):
			old_path = event.src_path
			gallery = gallerydb.GalleryDB.get_gallery_by_path(old_path)
			if gallery:
				self.MOVED_SIGNAL.emit(event.dest_path, gallery)

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
