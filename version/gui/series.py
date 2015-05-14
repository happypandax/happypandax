from PyQt5.QtCore import (Qt, QAbstractListModel, QModelIndex, QVariant,
						  QSize, QRect, QEvent, pyqtSignal, QThread,
						  QTimer)
from PyQt5.QtGui import (QPixmap, QBrush, QColor, QPainter,
						 QFont, QPen, QTextDocument,
						 QMouseEvent, QHelpEvent,
						 QPixmapCache)
from PyQt5.QtWidgets import (QListView, QFrame, QLabel,
							 QStyledItemDelegate, QStyle,
							 QMenu, QAction, QToolTip,
							 QHBoxLayout, QVBoxLayout,
							 QWidget, QPushButton,
							 QSizePolicy, QTableWidget,
							 QTableWidgetItem)
from ..database import fetch, seriesdb
from . import gui_constants, misc

data_thread = QThread()
loading_thread = QThread()

def populate():
	"Populates the database with series from local drive'"
	loading = misc.Loading()
	if not loading.ON:
		misc.Loading.ON = True
		fetch_instance = fetch.Fetch()
		loading.show()

		def finished(status):
			if status:
				SeriesModel.update_data()
				# TODO: make it spawn a dialog instead (from utils.py or misc.py)
				if loading.progress.maximum() == loading.progress.value():
					misc.Loading.ON = False
					loading.hide()
				data_thread.quit
			else:
				loading.setText("<font color=red>An error occured. Try restarting..</font>")
				loading.progress.setStyleSheet("background-color:red")
				data_thread.quit

		def fetch_deleteLater():
			fetch_instance.deleteLater

		def thread_deleteLater(): #NOTE: Isn't this bad?
			data_thread.deleteLater

		def a_progress(prog):
			loading.progress.setValue(prog)
			loading.setText("Searching on local disk...\n(Will take a while on first time)")

		fetch_instance.moveToThread(data_thread)
		fetch_instance.DATA_COUNT.connect(loading.progress.setMaximum)
		fetch_instance.PROGRESS.connect(a_progress)
		data_thread.started.connect(fetch_instance.local)
		fetch_instance.FINISHED.connect(finished)
		fetch_instance.FINISHED.connect(fetch_deleteLater)
		fetch_instance.FINISHED.connect(thread_deleteLater)
		data_thread.start()


class SeriesModel(QAbstractListModel):
	"""Model for Model/View/Delegate framework
	"""
	_data = [] #a list for the data

	def __init__(self, parent=None):
		super().__init__(parent)
		self._data_count = 0 # number of items added to model
		self.update_data()
		#self._data_container = []

	@classmethod
	def update_data(self):
		"Populates the model with data from database"
		self._data = seriesdb.SeriesDB.get_all_series()

	def data(self, index, role):
		if not index.isValid():
			return QVariant()
		if index.row() >= len(self._data) or \
			index.row() < 0:
			return QVariant()

		current_row = index.row() 
		current_series = self._data[current_row]

		if role == Qt.DisplayRole:
			title = current_series.title
			artist = current_series.artist
			text = {'title':title, 'artist':artist}
			return text
		if role == Qt.DecorationRole:
			pixmap = current_series.profile
			return pixmap
		if role == Qt.BackgroundRole:
			bg_color = QColor(70, 67, 70)
			bg_brush = QBrush(bg_color)
			return bg_brush
		#if role == Qt.ToolTipRole:
		#	return "Example popup!!"
		if role == Qt.UserRole+1:
			return current_series

		return None

	def rowCount(self, index = QModelIndex()):
		return self._data_count

	def flags(self, index):
		if not index.isValid():
			return Qt.ItemIsEnabled
		return Qt.ItemFlags(QAbstractListModel.flags(self, index) |
					  Qt.ItemIsEditable)

	def setData(self, index, value, role = Qt.EditRole):
		"""Takes the new data and appends it to old
		Note: Might want to make make it replace instead"""
		super().setData(self)
		#NOTE: Things are more complicated than this
		#if index.isValid() and 0 <= index.row() < len(self._data):
		#	current_row = index.row()
		#	current_data = self._data[current_row]
		#	self._data.append(value)
		#	self.dataChanged.emit(index, index, ()) # emit a tuple of roles that have changed in 3rd arg
		#	return True
		#return False

	def insertRows(self, position, value, rows=1, index = QModelIndex()):
		self.beginInsertRows(QModelIndex(), position, position + rows - 1)
		for row in range(rows):
			self._data.append(value[row])
		self.endInsertRows()
		return True

	#def removeRows(self, int, int2, parent = QModelIndex()):
	#	pass

	#def sortBy(self, str):
	#	"""takes on of the following string as param
	#	str <- 'title', 'metadata', 'artist', 'last read', 'newest'"""
	#	pass


	def canFetchMore(self, index):
		if self._data_count < len(self._data):
			return True
		else: 
			return False

	def fetchMore(self, index):
		diff = len(self._data) - self._data_count
		item_to_fetch = min(50, diff)

		self.beginInsertRows(index, self._data_count,
					   self._data_count+item_to_fetch-1)
		self._data_count += item_to_fetch
		self.endInsertRows()

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
		self.W = gui_constants.THUMB_W_SIZE
		self.H = gui_constants.THUMB_H_SIZE
		self._state = None
		QPixmapCache.setCacheLimit(gui_constants.THUMBNAIL_CACHE_SIZE)
		self._painted_indexes = {}

	def key(self, index):
		"Assigns an unique key to indexes"
		if index in self._painted_indexes:
			return self._painted_indexes[index]
		else:
			id = str(len(self._painted_indexes))
			self._painted_indexes[index] = id
			return self._painted_indexes[index]

	def paint(self, painter, option, index):
		self.initStyleOption(option, index)

		self.text = index.data(Qt.DisplayRole)
		popup = index.data(Qt.ToolTipRole)
		title = self.text['title']
		artist = self.text['artist']

		# Enable this to see the defining box
		#painter.drawRect(option.rect)

		# define font size
		if 30 > len(title) > 20:
			title_size = "font-size:12px;"
		elif 40 > len(title) >= 30:
			title_size = "font-size:11px;"
		elif 50 > len(title) >= 40:
			title_size = "font-size:10px;"
		elif len(title) >= 50:
			title_size = "font-size:8px;"
		else:
			title_size = ""

		if 30 > len(artist) > 20:
			artist_size = "font-size:11px;"
		elif 40 > len(artist) >= 30:
			artist_size = "font-size:9px;"
		elif len(artist) >= 40:
			artist_size = "font-size:8px;"
		else:
			artist_size = ""

		#painter.setPen(QPen(Qt.NoPen))
		r = option.rect.adjusted(1, 0, -1, -1)
		rec = r.getRect()
		x = rec[0]
		y = rec[1] + 3
		w = rec[2]
		h = rec[3] - 5
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
		{}
		}}
		#artist {{
		position:absolute;
		color:white;
		top:20px;
		right:0;
		{}
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
		""".format(title_size, artist_size, title, artist, "Chapters"))
		text_area.setTextWidth(w)

		#chapter_area = QTextDocument()
		#chapter_area.setDefaultFont(option.font)
		#chapter_area.setHtml("""
		#<font color="black">{}</font>
		#""".format("chapter"))
		#chapter_area.setTextWidth(w)

		painter.setRenderHint(QPainter.SmoothPixmapTransform)

		# if we can't find a cached image
		if not isinstance(QPixmapCache.find(self.key(index)), QPixmap):
			self.image = QPixmap(index.data(Qt.DecorationRole))
			id = self.key(index)
			QPixmapCache.insert(id, self.image)
			if self.image.height() < self.image.width(): #to keep aspect ratio
				painter.drawPixmap(QRect(x, y, w, self.image.height()),
						self.image)
			else:
				painter.drawPixmap(QRect(x, y, w, h),
						self.image)
		else:
			self.image = QPixmapCache.find(self.key(index))
			if self.image.height() < self.image.width(): #to keep aspect ratio
				painter.drawPixmap(QRect(x, y, w, self.image.height()),
						self.image)
			else:
				painter.drawPixmap(QRect(x, y, w, h),
						self.image)

		#draw the label for text
		painter.save()
		painter.translate(option.rect.x(), option.rect.y()+140)
		box_color = QBrush(QColor(0,0,0,123))
		painter.setBrush(box_color)
		rect = QRect(0, 0, w+2, 60) #x, y, width, height
		painter.fillRect(rect, box_color)
		painter.restore()
		painter.save()
		# draw text
		painter.translate(option.rect.x(), option.rect.y()+142)
		text_area.drawContents(painter)
		painter.restore()

		if option.state & QStyle.State_MouseOver:
			painter.fillRect(option.rect, QColor(225,225,225,90)) #70

		if option.state & QStyle.State_Selected:
			painter.fillRect(option.rect, QColor(164,164,164,120)) #option.palette.highlight()

		if option.state & QStyle.State_Selected:
			painter.setPen(QPen(option.palette.highlightedText().color()))

	def sizeHint(self, QStyleOptionViewItem, QModelIndex):
		return QSize(self.W, self.H)


	def editorEvent(self, event, model, option, index):
		"Mouse events for each item in the view are defined here"
		if event.type() == QEvent.MouseButtonPress:
			mouseEvent = QMouseEvent(event)
			if mouseEvent.buttons() == Qt.LeftButton:
				self._state = (index.row(), index.column())
				from ..constants import WINDOW
				self.BUTTON_CLICKED.emit(WINDOW.setCurrentIndex(1, index))#self._state)
				print("Clicked")
				return True
			else: return super().editorEvent(event, model, option, index)
		else:
			return super().editorEvent(event, model, option, index)


class MangaView(QListView):
	"""
	TODO: (zoom-in/zoom-out) mousekeys
	"""
	def __init__(self, parent=None):
		super().__init__(parent)
		self.setViewMode(self.IconMode)
		self.H = gui_constants.GRIDBOX_H_SIZE
		self.W = gui_constants.GRIDBOX_W_SIZE
		self.setGridSize(QSize(self.W, self.H))
		self.setSpacing(10)
		self.setResizeMode(self.Adjust)
		# all items have the same size (perfomance)
		self.setUniformItemSizes(True)
		# improve scrolling
		self.setVerticalScrollMode(self.ScrollPerPixel)
		self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		# prevent all items being loaded at the same time
		#self.setLayoutMode(self.Batched)
		#self.setBatchSize(15) #Only loads 20 images at a time
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
	#	#if event.type() == QEvent.ToolTip:
	#	#	help_event = QHelpEvent(event)
	#	#	index = self.indexAt(help_event.globalPos())
	#	#	if index is not -1:
	#	#		QToolTip.showText(help_event.globalPos(), "Tooltip!")
	#	#	else:
	#	#		QToolTip().hideText()
	#	#		event.ignore()
	#	#	return True
	#	if event.type() == QEvent.Enter:
	#		print("hovered")
	#	else:
	#		return super().event(event)

	def entered(*args, **kwargs):
		return super().entered(**kwargs)

class ChapterView(MangaView):
	"A view for chapters"
	def __init__(self, parent=None):
		super().__init__()


class ChapterInfo(QFrame):
	"A view for chapter data"
	def __init__(self, parent=None):
		super().__init__(parent)
		self.H = gui_constants.CHAP_IMAGE_H
		self.W = self.H//1.6
		self.setFrameStyle(1)
		self.setLineWidth(1)
		self.setMaximumWidth(self.W*1.2)
		#self.data = []
		self.initUI()

	def display_manga(self, index):
		"""Receives a QModelIndex and updates the
		viewport with specific manga data"""
		series = index.data(Qt.UserRole+1)
		self.drawContents(series)

	def initUI(self):
		"Constructs UI for the chapter info view"
		background_layout = QVBoxLayout()
		self.setLayout(background_layout)
		

		# The image
		self.image_icon_size = QSize(self.W, self.H)
		self.image_box = QLabel()
		background_layout.addWidget(self.image_box, 0, Qt.AlignHCenter)

		# the metadata
		self.metadata = QTableWidget()
		self.metadata.setRowCount(10)
		self.metadata.setColumnCount(2)
		#self.metadata.setColumnWidth(2,70)
		#self.metadata.resizeColumnsToContents()
		self.metadata.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
		self.metadata.setShowGrid(False)
		self.metadata.horizontalHeader().setVisible(False)
		self.metadata.verticalHeader().setVisible(False)
		self.metadata.setFrameShape(QFrame.NoFrame)
		self.metadata.setFocusPolicy(Qt.NoFocus)
		self.metadata.setWordWrap(True)
		background_layout.addWidget(self.metadata, 2)

		def t_props(obj):
			obj.setWordWrap(True)

		self.title = QLabel()
		t_props(self.title)
		self.title.setAlignment(Qt.AlignHCenter)
		self.metadata.setCellWidget(0,0,self.title)
		self.metadata.setSpan(0,0,1,2)

		self.artist = QLabel()
		self.artist.setAlignment(Qt.AlignLeft)
		self.metadata.setCellWidget(1,0, self.artist)

		self.chapter_count = QLabel()
		self.chapter_count.setAlignment(Qt.AlignRight)
		self.metadata.setCellWidget(1, 1, self.chapter_count)

		self.info = QLabel()
		self.info.setAlignment(Qt.AlignLeft)
		t_props(self.info)
		self.metadata.setCellWidget(2,0, self.info)
		self.metadata.setSpan(2,0,1,2)

		#self.last_read = QLabel("None")
		#self.last_update = QLabel("None")

		self.date_added = QLabel()
		self.date_added.setAlignment(Qt.AlignLeft)
		self.metadata.setCellWidget(3,0, self.date_added)

		self.pub_date = QLabel()
		self.pub_date.setAlignment(Qt.AlignRight)
		self.metadata.setCellWidget(3,1, self.pub_date)

		self.tags = QLabel()
		t_props(self.tags)
		self.tags.setAlignment(Qt.AlignLeft)
		self.metadata.setCellWidget(4,0, self.tags)
		self.metadata.setSpan(4, 0, 1, 2)

		self.path = QLabel()
		t_props(self.path)
		self.path.setAlignment(Qt.AlignLeft)
		self.metadata.setCellWidget(5,0, self.path)
		self.metadata.setSpan(5,0,1,2)


	def drawContents(self, series):
		assert isinstance(series, seriesdb.Series), "Please provide a series of Series class from SeriesDB"
		
		new_image = QPixmap(series.profile).scaled(self.image_icon_size, Qt.KeepAspectRatio,
					Qt.SmoothTransformation)
		self.image_box.setPixmap(new_image)
		self.title.setText("<font size='4' color='#585858'><b>"+series.title+"</b></font>")
		self.artist.setText("<font size='3' color='#585858'>"+series.artist+"</font>")
		self.chapter_count.setText("<font size='2' color='#B7153E'><i>Chapters:</i></font>"+"TODO")
		self.info.setText("<font size='2' color='#B7153E'><i>Description:</i></font><br>"+series.info)
		self.date_added.setText("<font size='2' color='#B7153E'><i>Date Added:</i></font><br>"+series.date_added)
		self.pub_date.setText("<font size='2' color='#B7153E'><i>Date Published:</i></font><br>"+series.pub_date)
		self.tags.setText("<font size='2' color='#B7153E'><i>Tags:</i></font><br>"+"TODO")
		self.path.setText("<font size='2' color='#B7153E'><i>Path:</i></font><br><font size='2'><i>"+series.path+"</i></font><br>")
		#self.path.setText("Path:\n"+series.path)
		self.metadata.resizeRowsToContents()

	#def resizeEvent(self, resizeevent):
	#	"""This method basically need to make sure
	#	the image in chapter view gets resized when moving
	#	splitter"""
	#	super().resizeEvent(resizeevent)
	#	self.MAIN_SIZE = resizeevent.size()


if __name__ == '__main__':
	raise NotImplementedError("Unit testing not yet implemented")
