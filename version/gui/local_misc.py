from PyQt5.QtCore import QFileSystemWatcher

from . import gui_constants
from ..database import gallerydb

class PathWatcher:
	def __init__(self, **kwargs):
		self.watcher = QFileSystemWatcher()
		if gui_constants.MONITOR_PATHS[0]:
			self.watcher.addPaths(gui_constants.MONITOR_PATHS)

		self.gallery_watcher = QFileSystemWatcher()
		galleries = gallerydb.GalleryDB.get_all_gallery()
		for gallery in galleries:
			self.gallery_watcher.addPath(gallery.path)
		self.gallery_watcher.directoryChanged.connect(self.test)
		self.gallery_watcher.fileChanged.connect(self.test)
		print(len(self.gallery_watcher.directories()))
	def test(self, path):
		print(path)