from PyQt5.QtCore import (Qt, QAbstractListModel)
from PyQt5.QtGui import (QPixmap)
from PyQt5.QtWidgets import (QAbstractItemView, QAbstractItemDelegate,
							 QAbstractButton)

class GridBox(QAbstractButton):
	"""A Manga/Chapter box
	pixmap <- the image in full resolution (a pixmap object)
	title <- str
	metadata <- dict ( e.g. ["d])
	"""
	def __init__(self, pixmap, title, artist, metadata,
			  parent=None):
		super().__init__(parent)
		self.pixmap = pixmap
		self.title = title
		self.artist = artist
		self.metadata = metadata
		

	def paintEvent(self, event):
		painter = QPainter(self)
		painter.drawPixmap() #event.rect(), self.pixmap)


	def sizeHint(self):
		return self.pixmap.size()



class _Manga(QAbstractListModel):
	pass

class _Chapter(QAbstractListModel):
	pass