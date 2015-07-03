import logging, os
from PyQt5.QtCore import Qt, QObject, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout,
							 QLabel, QFrame, QPushButton)
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from . import gui_constants, misc
from ..database import gallerydb

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical

class BasePopup(QWidget):
	def __init__(self, parent=None):
		super().__init__(parent, flags= Qt.Window | Qt.FramelessWindowHint)
		self.setAttribute(Qt.WA_TranslucentBackground)
		main_layout = QVBoxLayout()
		self.main_widget = QFrame()
		self.setLayout(main_layout)
		main_layout.addWidget(self.main_widget)
		self.button_layout = QHBoxLayout()
		self.button_layout.addWidget(misc.Spacer('h'))
		self.yes_button = QPushButton('Yes')
		self.no_button = QPushButton('No')
		self.button_layout.addWidget(self.yes_button)
		self.button_layout.addWidget(self.no_button)
		self.setMaximumWidth(500)
		self.resize(500,350)


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
		main_layout = QVBoxLayout()
		name = os.path.split(path)[1]
		info_lbl = QLabel('New gallery detected!\n\n{}\n\nDo you want to add it?'.format(name))
		info_lbl.setWordWrap(True)
		info_lbl.setAlignment(Qt.AlignCenter)
		main_layout.addWidget(info_lbl)
		main_layout.addLayout(self.button_layout)
		self.main_widget.setLayout(main_layout)
		def add():
			self.ADD_SIGNAL.emit(path)
		self.yes_button.clicked.connect(add)
		self.no_button.clicked.connect(self.close)
		self.adjustSize()
		self.show()

class MovedPopup(BasePopup):
	def __init__(self, path, gallery_id, parent=None):
		super().__init__(parent)
		main_layout = QVBoxLayout()
		main_layout.addWidget(QLabel("Moved:\npath: {}\nID:{}".format(path, gallery_id)))
		self.main_widget.setLayout(main_layout)

		self.show()

class DeletedPopup(BasePopup):
	def __init__(self, path, gallery_id, parent=None):
		super().__init__(parent)
		main_layout = QVBoxLayout()
		main_layout.addWidget(QLabel("Deleted:\npath: {}\nID:{}".format(path, gallery_id)))
		self.main_widget.setLayout(main_layout)
		self.show()


class GalleryHandler(FileSystemEventHandler, QObject):
	CREATE_SIGNAL = pyqtSignal(str)
	MODIFIED_SIGNAL = pyqtSignal(str, int)
	DELETED_SIGNAL = pyqtSignal(str, int)
	MOVED_SIGNAL = pyqtSignal(str, int)

	def __init__(self):
		super().__init__()

	def on_created(self, event):
		self.CREATE_SIGNAL.emit(event.src_path)

	def on_deleted(self, event):
		self.DELETED_SIGNAL.emit(event.src_path, 1)

	def on_modified(self, event):
		self.MODIFIED_SIGNAL.emit('modified', 1)

	def on_moved(self, event):
		self.MOVED_SIGNAL.emit('hi', 2)

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
