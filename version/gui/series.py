from PyQt5.QtCore import (Qt, QAbstractListModel, QModelIndex, QVariant,
						  QSize, QRect, QRectF)
from PyQt5.QtGui import (QPixmap, QIcon, QBrush, QRadialGradient,
						 QColor, QPainter, QFont, QPen, QTextDocument)
from PyQt5.QtWidgets import (QListView, QAbstractItemDelegate,
							 QFrame, QLabel, QStyledItemDelegate,
							 QStyle, QApplication, QItemDelegate)
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
		self._data = []
		self.pic = QPixmap() #IMAGE PATH HERE
		self.modified_pic = self.pic
		paint = QPainter(self.modified_pic)
		paint.setRenderHint(QPainter.TextAntialiasing)
		font = paint.font()
		paint.setFont(font)
		init_font_size = font.pointSize()
		def font_size(x):
			font.setPointSize(init_font_size*x)
			paint.setFont(font)
		
		for x in range(30):
			title = "Title {}".format(x)
			artist = "Arist {}".format(x)
			paint.setPen(Qt.blue)
			pos1 = self.modified_pic.height()-200
			pos2 = pos1 + 120
			font_size(14)
			paint.drawText(20, pos1, title)
			font_size(12)
			paint.drawText(20, pos2, artist)
			#self._data.append(QIcon(self.modified_pic))
			self._data.append([(title, artist),
					  QIcon(self.modified_pic)])

	def data(self, index, role):
		if not index.isValid() or \
			not (0 <= index.row() < len(self._data)):
			return QVariant()

		current_row = index.row()
		current_data = self._data[current_row]
		metadata = current_data[0]
		pixmap = current_data[1]

		if role == Qt.DisplayRole:
			return metadata
		if role == Qt.DecorationRole:
			return pixmap
		if role == Qt.BackgroundRole:
			bg_color = QColor(70, 67, 70)
			bg_brush = QBrush(bg_color)
			return bg_brush
		return None

	def rowCount(self, parent = QModelIndex()):
		return len(self._data)

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

class CustomDelegate(QStyledItemDelegate):
	"A custom delegate for the model/view framework"
	def __init__(self):
		super().__init__()

	def paint(self, painter, option, index):
		image = index.data(Qt.DecorationRole)
		text = index.data(Qt.DisplayRole)
		title = text[0]
		artist = text[1]

		painter.setRenderHint(QPainter.Antialiasing)
		painter.drawRect(option.rect)
		palette = QApplication.palette()
		#painter.setPen(QPen(Qt.NoPen))

		r = option.rect
		rec = r.getRect()
		x = rec[0]
		y = rec[1]
		w = rec[2]
		h = rec[3]
		painter.setRenderHint(QPainter.TextAntialiasing)
		
		text_area = QTextDocument()
		text_area.setDefaultFont(option.font)
		painter.save()
		text_area.setHtml("<font color=black> {} </font>".format(title))

		#image.paint(painter, QRect(x, y, w, h))#QRect(x, y, w, h))

		color = palette.highlight().color()
		# draw text
		#painter.fillRect(option.rect, color)
		painter.translate(option.rect.x(), option.rect.y())
		text_area.drawContents(painter, QRectF(-10, -50, 100, 100))
		#painter.drawText(w//3,h + 10, title)
		#painter.drawText(w//3,h + 25, artist)
		painter.restore()
		#QStyledItemDelegate.paint(self, painter, option, index)

	def sizeHint(self, QStyleOptionViewItem, QModelIndex):
		return QSize(150, 200)


class Display(QListView):
	"""TODO: Inherit QListView, and add grid view functionalities
	hint: add resize funtionality extra: (zoom-in/zoom-out) mousekeys
	"""
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setViewMode(self.IconMode)
		self.setGridSize(QSize(200, 200))
		self.setSpacing(10)
		self.setResizeMode(self.Adjust)
		# all items have the same size (perfomance)
		self.setUniformItemSizes(True)

if __name__ == '__main__':
	raise NotImplementedError("Unit testing not yet implemented")