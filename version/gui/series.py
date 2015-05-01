from PyQt5.QtCore import (Qt, QAbstractListModel, QModelIndex, QVariant,
						  QSize, QRect, QRectF, QEvent, pyqtSignal)
from PyQt5.QtGui import (QPixmap, QIcon, QBrush, QRadialGradient,
						 QColor, QPainter, QFont, QPen, QTextDocument,
						 QMouseEvent, QHelpEvent)
from PyQt5.QtWidgets import (QListView, QAbstractItemDelegate,
							 QFrame, QLabel, QStyledItemDelegate,
							 QStyle, QApplication, QItemDelegate,
							 QListWidget, QMenu, QAction, QToolTip,
							 QHBoxLayout, QVBoxLayout, QWidget)
from ..database import fetch
from . import gui_constants
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

# Seems to be obselete
class GridBox(QFrame):
	"""Defines gridboxes; Data to be used by SeriesModel.
	Receives an object of <Manga> class defined in database/manga.py
	CANDIDATE FOR OBSELENCE"""
	def __init__(self, object):
		super().__init__()
		# useless with QIcon
		#self.pixmap = object.pixmap
		#self.pixmap_huge = None
		#self.pixmap_big = None
		#self.pixmap_medium = None
		#self.pixmap_small = None
		#self.pixmap_micro = None
		#self.current_pixmap = None
		#self._do_pixmap() # create the different image sizes

		self.title = object.get_title
		self.artist = object.get_artist
		self.chapters = object.chapter_count
		self.date_added = object.date_added
		self.last_read = object.last_read

		self.setFrameStyle(self.StyledPanel)

	#def _do_pixmap(self):
	#	"""Creates the different image sizes.
	#	Note: Probably need to move this to database,
	#	and have it be predefined for perfomance gains.
	#	"""
	#	pass

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
		self._data = [] # a list for the data
		self.pic = QPixmap(gui_constants.PIXMAP_PATH) # the image for gridbox
		self.modified_pic = self.pic # was meant for when i wanted to draw on the pic
		
		#Test data
		#for x in range(100):
		#	title = "Title {}".format(x)
		#	artist = "Arist {}".format(x)
			#paint.setPen(Qt.blue)
			#pos1 = self.modified_pic.height()-200
			#pos2 = pos1 + 120
			#font_size(14)
			#paint.drawText(20, pos1, title)
			#font_size(12)
			#paint.drawText(20, pos2, artist)
			#self._data.append(QIcon(self.modified_pic))
		#	self._data.append([(title, artist),
		#			  QIcon(self.modified_pic)])

		# temporarily moving this to populate method
		#local data
		#local_series = fetch.local() #move to seperate function later
		#for series in local_series:
		#	self._data.append([(series.title, series.artist),
		#			  QPixmap(series.title_image)])

	def data(self, index, role):
		if not index.isValid() or \
			not (0 <= index.row() < len(self._data)): # to make sure we get valid indexes
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
		if role == Qt.ToolTipRole:
			return "Example popup!!"
		if role == Qt.UserRole+1:
			#this needs to be replaced by real metadata
			test_data = {"date_added":"01 May 2015", "chapters":"30",
				"year":"2015"}
			return index

		return None

	def rowCount(self, index = QModelIndex()):
		return len(self._data)

	def flags(self, index):
		if not index.isValid():
			return Qt.ItemIsEnabled
		return Qt.ItemFlags(QAbstractListModel.flags(self, index) |
					  Qt.ItemIsEditable)

	def setData(self, index, value, role = Qt.EditRole):
		"""Takes the new data and appends it to old
		Note: Might want to make make it replace instead"""
		if index.isValid() and 0 <= index.row() < len(self._data):
			current_row = index.row()
			current_data = self._data[current_row]
			self._data.append(value)
			self.dataChanged.emit(index, index, ()) # emit a tuple of roles that have changed in 3rd arg
			return True
		return False

	def insertRows(self, position, value, rows=1, index = QModelIndex()):
		self.beginInsertRows(QModelIndex(), position, position + rows - 1)
		for row in range(rows):
			self._data.insert(position + row, value)
		self.endInsertRows()
		return True

	#def removeRows(self, int, int2, parent = QModelIndex()):
	#	pass

	def sortBy(self, str):
		"""takes on of the following string as param
		str <- 'title', 'metadata', 'artist', 'last read', 'newest'"""
		pass

	def populate(self):
		"Populates from local series'"
		local_series = fetch.local()
		row = self.rowCount()
		for series in local_series:
			row += 1
			value = [(series.title, series.artist), QPixmap(series.title_image)]
			self.insertRows(row, value)

	def save(self):
		"Appends to DB for save"
		pass

class ChapterModel(SeriesModel):
	pass

class CustomDelegate(QStyledItemDelegate):
	"A custom delegate for the model/view framework"

	BUTTON_CLICKED = pyqtSignal(int)

	def __init__(self):
		super().__init__()
		self.W = 145
		self.H = 200
		self._state = None

	def paint(self, painter, option, index):
		self.initStyleOption(option, index)
		self.image = QIcon(index.data(Qt.DecorationRole))
		self.text = index.data(Qt.DisplayRole)
		popup = index.data(Qt.ToolTipRole)
		title = self.text[0]
		artist = self.text[1]

		painter.setRenderHint(QPainter.Antialiasing)
		# Enable this to see the defining box
		#painter.drawRect(option.rect)

		#painter.setPen(QPen(Qt.NoPen))

		r = option.rect.adjusted(1, 0, -1, -1)
		rec = r.getRect()
		x = rec[0]
		y = rec[1] + 3
		w = rec[2]
		h = rec[3] - 5
		painter.setRenderHint(QPainter.TextAntialiasing)
		#title="LongLongngLongTextLongLongText"
		#colors: title: #323232 artist: #585858
		text_area = QTextDocument()
		text_area.setDefaultFont(option.font)
		text_area.setHtml("""
		<head>
		<style>
		#area
		{{
			display:flex;
			width:140px;
			height:10px
		}}
		#title {{
		position:absolute;
		color: white;
		font-weight:bold;
		}}
		#artist {{
		position:absolute;
		color:white;
		top:20px;
		right:0;
		}}
		</style>
		</head>
		<body>
		<div id="area">
		<center>
		<div id="title">{}
		</div>
		<div id="artist">{}
		</div>
		</div>
		</center>
		</body>
		""".format(title, artist, "Chapters"))
		text_area.setTextWidth(w)

		chapter_area = QTextDocument()
		chapter_area.setDefaultFont(option.font)
		chapter_area.setHtml("""
		<font color="black">{}</font>
		""".format("chapter"))
		chapter_area.setTextWidth(w)

		self.image.paint(painter, QRect(x, y, w, h))

		#draw the label for text
		painter.save()
		painter.translate(option.rect.x(), option.rect.y()+140)
		box_color = QBrush(QColor(0,0,0,123))
		painter.setBrush(box_color)
		rect = QRect(0, 0, w+2, 60) #x, y, width, height
		#painter.drawRect(rect)
		painter.fillRect(rect, box_color)
		painter.restore()
		painter.save()
		# draw text
		painter.translate(option.rect.x(), option.rect.y()+150)
		text_area.drawContents(painter)
		painter.restore()
		
		if option.state & QStyle.State_MouseOver:
			painter.fillRect(option.rect, QColor(225,225,225,70)) #option.palette.highlight()

		if option.state & QStyle.State_Selected:
			painter.fillRect(option.rect, QColor(164,164,164,120)) #option.palette.highlight()

		if option.state & QStyle.State_Selected:
			painter.setPen(QPen(option.palette.highlightedText().color()))

	def sizeHint(self, QStyleOptionViewItem, QModelIndex):
		return QSize(self.W, self.H)

	def editorEvent(self, event, model, option, index):
		"Mouse events for each item in the view are defined here"
		if event.type() == QEvent.MouseButtonPress:
			self._state = (index.row(), index.column())
			from ..constants import WINDOW
			self.BUTTON_CLICKED.emit(WINDOW.setCurrentIndex(1, index))#self._state)
			print("Clicked")
			return True
		else:
			return super().editorEvent(event, model, option, index)
		#elif event.type() == QEvent.MouseButtonRelease:
		#	if self._state == (index.row(), index.column()):
		#		self.BUTTON_CLICKED.emit(self._state)
		#		return True
		#	elif self._state:
		#		old_index = index.model().index(self._state)
		#		self._state = None
		#		index.model().dataChanged.emit(old_index, old_index)
		#	self._state = None
		#	return True
		#else:
		#	return super().editorEvent(event, model, option, index)

class MangaView(QListView):
	"""
	TODO: (zoom-in/zoom-out) mousekeys
	"""
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setViewMode(self.IconMode)
		self.H = 250
		self.W = self.H//1.47
		self.setGridSize(QSize(self.W, self.H))
		self.setSpacing(10)
		self.setResizeMode(self.Adjust)
		# all items have the same size (perfomance)
		self.setUniformItemSizes(True)
		# improve scrolling
		self.setVerticalScrollMode(self.ScrollPerPixel)
		# prevent all items being loaded at the same time
		self.setLayoutMode(self.Batched)
		#self.setBatchSize(100) Only loads 100 images at a time
		self.setWordWrap(True)
		self.setMouseTracking(True)

	def foo(self):
		pass

	def contextMenuEvent(self, event):
		handled = False
		custom = False
		index = self.indexAt(event.pos())
		menu = QMenu()
		all = QAction("Remove", menu, triggered = self.foo)
		if index.row() in [j for j in range(10)]:
			action_1 = QAction("Awesome!", menu, triggered = self.foo)
			action_2 = QAction("It just werks!", menu, triggered = self.foo)
			menu.addActions([action_1, action_2])
			handled = True
			custom = True
		else:
			add_series = QAction("&Add new Series...", menu,
						triggered = self.foo)
			menu.addAction(add_series)
			handled = True

		if handled and custom:
			menu.addAction(all)
			menu.exec_(event.globalPos())
			event.accept()
		elif handled:
			menu.exec_(event.globalPos())
			event.accept()
		else:
			event.ignore()

	#need this for debugging purposes
	def resizeEvent(self, resizeevent):
		super().resizeEvent(resizeevent)
		#print(resizeevent.size())

	#unusable code
	#def event(self, event):
	#	if event.type() == QEvent.ToolTip:
	#		help_event = QHelpEvent(event)
	#		index = self.indexAt(help_event.globalPos())
	#		if index is not -1:
	#			QToolTip.showText(help_event.globalPos(), "Tooltip!")
	#		else:
	#			QToolTip().hideText()
	#			event.ignore()
	#		return True
	#	else:
	#		return super().event(event)

class ChapterView(MangaView):
	"A view for chapters"
	def __init__(self, parent=None):
		super().__init__()


class ChapterUpper(QFrame):
	"A view for chapter data"
	def __init__(self, parent=None):
		super().__init__(parent)
		height = 250
		self.H = height
		self.setMaximumHeight(height)
		self.setFrameStyle(1)
		self.setLineWidth(1)
		#self.data = []
		self.initUI()

	def display_manga(self, index):
		"""Receives a QModelIndex and updates the
		viewport with specific manga data"""
		self.image = index.data(Qt.DecorationRole)
		self.text = index.data(Qt.DisplayRole)
		self.metadata = index.data(Qt.UserRole+1)
		self.title = self.text[0]
		self.artist = self.text[1]
		self.drawImage(self.image)

	def initUI(self):
		"Constructs UI for the chapter upper view"
		main_layout = QHBoxLayout()
		self.setLayout(main_layout)

		self.image_size = QSize(self.H//1.6, self.H)
		self.image_icon_size = QSize(self.H//1.6-2, self.H-2)

		self.image_box = QLabel()
		self.image_box.resize(self.image_size)

		main_layout.addWidget(self.image_box, 0, Qt.AlignHCenter)

	def drawImage(self, img):
		self.image = img
		self.new_image = self.image.scaled(self.image_icon_size, Qt.KeepAspectRatio,
					Qt.SmoothTransformation)
		self.image_box.setPixmap(self.new_image)


	def resizeEvent(self, resizeevent):
		"""This method basically need to make sure
		the image in chapter view gets resized when moving
		splitter"""
		super().resizeEvent(resizeevent)
		self.MAIN_SIZE = resizeevent.size()
		self.H = self.MAIN_SIZE.height()

		#for debugging purposes
		#print("Old Size: ", resizeevent.oldSize())
		#print("New Size: ", resizeevent.size())


if __name__ == '__main__':
	raise NotImplementedError("Unit testing not yet implemented")
