from PyQt5.QtCore import (Qt, QAbstractListModel, QModelIndex, QVariant)
from PyQt5.QtGui import (QPixmap)
from PyQt5.QtWidgets import (QAbstractItemView, QAbstractItemDelegate,
							 QFrame, QLabel)
from ..database.seriesdb import Manga

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
		self.pixmap = object.pixmap
		self.pixmap_huge = None
		self.pixmap_big = None
		self.pixmap_medium = None
		self.pixmap_small = None
		self.pixmap_micro = None
		self.current_pixmap = None
		self._do_pixmap() # create the different image sizes

		self.title = object.get_title
		self.artist = object.get_artist
		self.chapters = object.chapter_count
		self.date_added = object.date_added
		self.last_read = object.last_read

		self.setFrameStyle(self.StyledPanel)

	def _do_pixmap(self):
		"""Creates the different image sizes.
		Note: Probably need to move this to database,
		and have it be predefined for perfomance gains.
		"""
		pass

	def initUI(self):
		self.pixmap_label = QLabel()
		self.pixmap_label.setPixmap(self.current_pixmap)
		self.pixmap_label.setScaledContents(True)
		self.title_label = QLabel()
		self.title_label.setText(self.title)
		self.title_label.setWordWrap(True)

	def sizeHint():
		"Provides a default size"
		pass

	def setSizePolicy(self, Policy, Policy1):
		pass

	def resize(self, string):
		"""Set pixmap size. Receives one of the following as string params:
		"huge", "big", "medium", "small", "micro"
		"""
		assert type(string) == str, "GridBox only accept strings!"
		accepted = ["huge", "big", "medium", "small", "micro"]
		if not string in accepted:
			raise AssertionError("GridBox only accepts: huge, big, medium, small or micro")
		if string == accepted[0]:
			self.current_pixmap = self.pixmap_huge
		elif string == accepted[1]:
			self.current_pixmap = self.pixmap_big
		elif string == accepted[2]:
			self.current_pixmap = self.pixmap_medium
		elif string == accepted[3]:
			self.current_pixmap = self.pixmap_small
		elif string == accepted[4]:
			self.current_pixmap = self.pixmap_micro


	def mousePressEvent(self, QMouseEvent):
		"""Control what to do when mouse is pressed in the widget
		TODO: make it go open chapter view for this manga
		"""
		return super().mousePressEvent()

	def mouseDoubleClickEvent(self, QMouseEvent):
		"""Control what to do when mouse is double clicked in the widget
		TODO: maybe some editing?
		"""
		return super().mouseDoubleClickEvent()


class SeriesModel(QAbstractListModel):
	def __init__(self, parent=None):
		"""Model for Model/View/Delegate framework
		"""
		super().__init__(parent)
		self.gridbox = []
		self.test = []
		for x in range(50):
			#a = ["Test1", "Test2", "Test3", "Test4"]
			self.test.append("TestX")

	def data(self, index, role = Qt.DisplayRole):
		if not index.isValid() or \
			not (0 <= index.row() < len(self.test)):
			return QVariant()

		gridbox = self.test[index.row()]
		if role == Qt.DisplayRole:
			return gridbox

	def rowCount(self, parent = QModelIndex()):
		return len(self.test)

	#def headerData(self, int, Orientation, role = Qt.DisplayRole):
	#	pass

	#def columnCount(self, parent = QModelIndex()):
	#	pass

	#def flags(self, QModelIndex):
	#	pass

	#def setData(self, QModelIndex, QVariant, role = Qt.EditRole):
	#	pass

	#def insertRows(self, int, int2, parent = QModelIndex()):
	#	pass

	#def removeRows(self, int, int2, parent = QModelIndex()):
	#	pass

	def sortBy(self, str):
		"""takes on of the following string as param
		str <- 'title', 'metadata', 'artist', 'last read', 'newest'"""
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