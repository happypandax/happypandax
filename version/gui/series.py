from PyQt5.QtCore import (Qt, QAbstractListModel, QModelIndex)
from PyQt5.QtGui import (QPixmap)
from PyQt5.QtWidgets import (QAbstractItemView, QAbstractItemDelegate,
							 QFrame)
from ..database.manga import Manga

#class GridBox(QAbstractButton):
#	"""A Manga/Chapter box
#	pixmap <- the image in full resolution (a pixmap object)
#	title <- str
#	metadata <- dict ( e.g. ["d])
#	"""
#	def __init__(self, pixmap, title, metadata,
#			  parent=None):
#		super().__init__(parent)
#		self.pixmap = pixmap
#		self.title = title
#		self.metadata = metadata

#	def paintEvent(self, event):
#		painter = QPainter(self)
#		painter.drawPixmap() #event.rect(), self.pixmap)

#	def sizeHint(self):
#		return self.pixmap.size()

class GridBox(QFrame):
	"""Defines gridboxes; Data to be used by SeriesModel.
	Receives an object of <Manga> class defined in database/manga.py
	"""
	def __init__(self, object):
		super().__init__()
		self.title = object.title


class SeriesModel(QAbstractListModel):
	def __init__(self, objects):
		"""Model for Model/View/Delegate framework
		params:
		mangas <- list of <Manga> class objects
		"""
		super().__init__()
		self.objects = objects
		self.artist = set() # to prevent duplicates in artist view

	def data(self, QModelIndex, role = Qt.DisplayRole):
		pass

	def rowCount(self, parent = QModelIndex()):
		pass

	def headerData(self, int, Orientation, role = Qt.DisplayRole):
		pass

	def columnCount(self, parent = QModelIndex()):
		pass

	def flags(self, QModelIndex):
		pass

	def setData(self, QModelIndex, QVariant, role = Qt.EditRole):
		pass

	def insertRows(self, int, int2, parent = QModelIndex()):
		pass

	def removeRows(self, int, int2, parent = QModelIndex()):
		pass

	def sortBy(self, str):
		"Sort by metadata <- str"
		pass

	def populate(self):
		"Populates from DB"
		pass

	def save(self):
		"Appends to DB for save"
		pass

class ChapterModel(SeriesModel):
	pass

if __name__ == '__main__':
	raise NotImplementedError("Unit testing not yet implemented")