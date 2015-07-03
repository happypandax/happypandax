import logging
from PyQt5.QtCore import QObject, pyqtSignal
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from . import gui_constants
from ..database import gallerydb

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical

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
