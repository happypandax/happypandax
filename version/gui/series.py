from PyQt5.QtCore import (Qt, QAbstractListModel, QModelIndex, QVariant,
						  QSize, QRect, QEvent, pyqtSignal, QThread,
						  QTimer, QPointF)
from PyQt5.QtGui import (QPixmap, QBrush, QColor, QPainter, 
						 QPen, QTextDocument,
						 QMouseEvent, QHelpEvent,
						 QPixmapCache, QCursor)
from PyQt5.QtWidgets import (QListView, QFrame, QLabel,
							 QStyledItemDelegate, QStyle,
							 QMenu, QAction, QToolTip, QVBoxLayout,
							 QSizePolicy, QTableWidget, QScrollArea,
							 QHBoxLayout, QFormLayout, QDesktopWidget,
							 QWidget)
from ..database import seriesdb
from . import gui_constants, misc
from .. import utils
import threading

class Popup(QWidget):
	def __init__(self):
		super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)
		self.setAttribute(Qt.WA_ShowWithoutActivating)
		self.initUI()
		self.setWindowModality(Qt.WindowModal)
		#self.resize(gui_constants.POPUP_WIDTH,gui_constants.POPUP_HEIGHT)
		self.setFixedWidth(gui_constants.POPUP_WIDTH)
		self.setMaximumHeight(gui_constants.POPUP_HEIGHT)
	
	def initUI(self):
		main_layout = QVBoxLayout()
		self.setLayout(main_layout)
		form_l = QFormLayout()
		main_layout.addLayout(form_l)
		self.title = QLabel()
		self.title.setWordWrap(True)
		self.title_lbl = QLabel("Title:")
		self.artist = QLabel()
		self.artist.setWordWrap(True)
		self.artist_lbl = QLabel("Author:")
		self.chapters = QLabel()
		self.chapters_lbl = QLabel("Chapters:")
		self.info = QLabel()
		self.info_lbl = QLabel("Description:")
		self.info.setWordWrap(True)

		type_status_l = QHBoxLayout()
		self.type = QLabel()
		type_status_l.addWidget(self.type, 0, Qt.AlignLeft)
		self.status = QLabel()
		type_status_l.addWidget(self.status, 0, Qt.AlignRight)

		self.tags = QLabel()
		self.tags.setTextFormat(Qt.RichText)
		self.tags.setWordWrap(True)
		self.tags_lbl = QLabel("Tags:")

		self.pub_date = QLabel()
		self.date_added = QLabel()

		form_l.addRow(self.title_lbl, self.title)
		form_l.addRow(self.artist_lbl, self.artist)
		form_l.addRow(self.chapters_lbl, self.chapters)
		form_l.addRow(self.info_lbl, self.info)
		form_l.addRow(self.tags_lbl, self.tags)

	def set_series(self, series):
		def tags_parser(tags):
			string = ""
			try:
				if len(tags['default']) > 0:
					has_default = True
				else:
					has_default = False
			except KeyError:
				has_default = False

			for namespace in tags:
				if namespace == 'default':
					for n, tag in enumerate(tags[namespace], 1):
						if n == 1:
							string = tag + string
						else:
							string = tag + ', ' + string
				else:
					if not has_default:
						string += '<b>'+namespace + ':</b> '
						has_default = True
					else:
						string += '<br><b>' + namespace + ':</b> '
					for n, tag in enumerate(tags[namespace], 1):
						if n != len(tags[namespace]):
							string += tag + ', '
						else:
							string += tag

			return string

		self.title.setText(series.title)
		self.artist.setText(series.artist)
		self.chapters.setText("{}".format(len(series.chapters)))
		self.info.setText(series.info)
		self.type.setText(series.type)
		self.status.setText(series.status)
		self.tags.setText(tags_parser(series.tags))

class SeriesModel(QAbstractListModel):
	"""Model for Model/View/Delegate framework
	"""

	ROWCOUNT_CHANGE = pyqtSignal()
	STATUSBAR_MSG = pyqtSignal(str)
	CUSTOM_STATUS_MSG = pyqtSignal(str)

	def __init__(self, parent=None):
		super().__init__(parent)
		self._data_count = 0 # number of items added to model
		self._data = [] #a list for the data
		self.populate_data()
		#self._data_container = []
		self.layoutChanged.connect(lambda: self.status_b_msg("Refreshed")) # quite a hack
		self.dataChanged.connect(lambda: self.status_b_msg("Edited"))
		self.CUSTOM_STATUS_MSG.connect(self.status_b_msg)

	def populate_data(self):
		"Populates the model with data from database"
		self._data = seriesdb.SeriesDB.get_all_series()
		self.layoutChanged.emit()
		self.ROWCOUNT_CHANGE.emit()

	def status_b_msg(self, msg):
		self.STATUSBAR_MSG.emit(msg)

	def data(self, index, role):
		if not index.isValid():
			return QVariant()
		if index.row() >= len(self._data) or \
			index.row() < 0:
			return QVariant()

		current_row = index.row() 
		current_series = self._data[current_row]

		# TODO: remove this.. not needed anymore, since i use custom role now
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

	#def flags(self, index):
	#	if not index.isValid():
	#		return Qt.ItemIsEnabled
	#	return Qt.ItemFlags(QAbstractListModel.flags(self, index) |
	#				  Qt.ItemIsEditable)

	def addRows(self, list_of_series, position=None,
				rows=1, index = QModelIndex()):
		"Adds new series data to model and to DB"
		from ..database.seriesdb import PROFILE_TO_MODEL
		if not position:
			position = len(self._data)
		self.beginInsertRows(QModelIndex(), position, position + rows - 1)
		for series in list_of_series:
			threading.Thread(target=seriesdb.SeriesDB.add_series_return, args=(series,)).start()
			series.profile = PROFILE_TO_MODEL.get()
			self._data.insert(0, series)
		self.endInsertRows()
		self.CUSTOM_STATUS_MSG.emit("Added row(s)")
		return True

	def insertRows(self, list_of_series, position,
				rows=1, index = QModelIndex()):
		"Inserts new series data to the data list WITHOUT adding to DB"
		self.beginInsertRows(QModelIndex(), position, position + rows - 1)
		for pos, series in enumerate(list_of_series, 1):
			self._data.insert(position+pos, n_series)
		self.endInsertRows()
		self.CUSTOM_STATUS_MSG.emit("Added row(s)")
		return True

	def replaceRows(self, list_of_series, position, rows=1, index=QModelIndex()):
		"replaces series data to the data list WITHOUT adding to DB"
		for pos, series in enumerate(list_of_series):
			del self._data[position+pos]
			self._data.insert(position+pos, series)
		self.dataChanged.emit(index, index, [Qt.UserRole+1])

	def removeRows(self, position, rows=1, index=QModelIndex()):
		self.beginRemoveRows(QModelIndex(), position, position + rows - 1)
		self._data = self._data[:position] + self._data[position + rows:]
		self._data_count -= rows
		self.endRemoveRows()
		return True

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
		item_to_fetch = min(gui_constants.PREFETCH_ITEM_AMOUNT, diff)

		self.beginInsertRows(index, self._data_count,
					   self._data_count+item_to_fetch-1)
		self._data_count += item_to_fetch
		self.endInsertRows()
		self.ROWCOUNT_CHANGE.emit()

class FavouriteModel(SeriesModel):
	def __init__(self):
		super().__init__()

	def populate_data(self):
		"Populates the model with data from database"
		self._data = seriesdb.SeriesDB.get_series_by_fav()
		self.layoutChanged.emit()
		self.ROWCOUNT_CHANGE.emit()

	def insertRows(self, list_of_series, position, rows = 1, index = QModelIndex()):
		pass

	def addRows(self, list_of_series, position = None, rows = 1, index = QModelIndex()):
		pass

	def replaceRows(self, list_of_series, position, rows=1, index=QModelIndex()):
		"Deletes the series from the view"
		for x in range(rows):
			self.removeRows(position+x, 1, index.parent())


class CustomDelegate(QStyledItemDelegate):
	"A custom delegate for the model/view framework"

	POPUP = pyqtSignal()
	CONTEXT_ON = False

	def __init__(self):
		super().__init__()
		self.W = gui_constants.THUMB_W_SIZE
		self.H = gui_constants.THUMB_H_SIZE
		QPixmapCache.setCacheLimit(gui_constants.THUMBNAIL_CACHE_SIZE)
		self._painted_indexes = {}
		self.popup_window = Popup()
		self.popup_timer = QTimer()
		#self.popup_timer.timeout.connect(self.POPUP.emit)

	def key(self, index):
		"Assigns an unique key to indexes"
		if index in self._painted_indexes:
			return self._painted_indexes[index]
		else:
			series_id = index.data(Qt.UserRole+1).id
			self._painted_indexes[index] = series_id
			return self._painted_indexes[index]

	def paint(self, painter, option, index):
		self.initStyleOption(option, index)

		assert isinstance(painter, QPainter)
		if index.data(Qt.UserRole+1):
			series = index.data(Qt.UserRole+1)
			popup = index.data(Qt.ToolTipRole)
			title = series.title
			artist = series.artist
			QRect.y
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


			# TODO: FIX THIS PART, MAYBE?
			# if we can't find a cached image
			#if not isinstance(QPixmapCache.find(self.key(index)), QPixmap):
			self.image = QPixmap(index.data(Qt.DecorationRole))
			#id = self.key(index)
			#QPixmapCache.insert(id, self.image)
			if self.image.height() < self.image.width(): #to keep aspect ratio
				painter.drawPixmap(QRect(x, y, w, self.image.height()),
						self.image)
			else:
				painter.drawPixmap(QRect(x, y, w, h),
						self.image)
			#else:
			#	self.image = QPixmapCache.find(self.key(index))
			#	if self.image.height() < self.image.width(): #to keep aspect ratio
			#		painter.drawPixmap(QRect(x, y, w, self.image.height()),
			#				self.image)
			#	else:
			#		painter.drawPixmap(QRect(x, y, w, h),
			#				self.image)
		
			# draw star if it's favourited
			if series.fav == 1:
				painter.drawPixmap(QPointF(x,y), QPixmap(gui_constants.STAR_PATH))

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
			else:
				self.popup_window.hide()
			#if option.state & QStyle.State_Selected:
			#	painter.fillRect(option.rect, QColor(164,164,164,120))

			#if option.state & QStyle.State_Selected:
			#	painter.setPen(QPen(option.palette.highlightedText().color()))
		else:
			super().paint(painter, option, index)

	def sizeHint(self, QStyleOptionViewItem, QModelIndex):
		return QSize(self.W, self.H)


class MangaView(QListView):
	"""
	TODO: (zoom-in/zoom-out) mousekeys
	"""

	STATUS_BAR_MSG = pyqtSignal(str)
	SERIES_DIALOG = pyqtSignal()

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
		self.manga_delegate = CustomDelegate()
		self.setItemDelegate(self.manga_delegate)
		self.series_model = SeriesModel()
		self.favourite_model = FavouriteModel()
		self.setModel(self.series_model)

		self.SERIES_DIALOG.connect(self.spawn_dialog)
		self.doubleClicked.connect(self.open_chapter)

	def foo(self):
		pass

	def remove_series(self, index):
		self.rowsAboutToBeRemoved(index.parent(), index.row(), index.row())
		self.model().removeRows(index.row(), 1)

	def favourite(self, index):
		assert isinstance(index, QModelIndex)
		series = index.data(Qt.UserRole+1)
		if self.model() == self.favourite_model:
			self.dataChanged(index, index)
			self.model().removeRows(index.row(), 1)
			self.model().CUSTOM_STATUS_MSG.emit("Unfavourited")
		else:
			if series.fav == 1:
				n_series = seriesdb.SeriesDB.fav_series_set(series.id, 0)
				self.model().replaceRows([n_series], index.row(), 1, index)
				self.model().CUSTOM_STATUS_MSG.emit("Unfavourited")
			else:
				n_series = seriesdb.SeriesDB.fav_series_set(series.id, 1)
				self.model().replaceRows([n_series], index.row(), 1, index)
				self.model().CUSTOM_STATUS_MSG.emit("Favourited")

	def open_chapter(self, index, chap_numb=0):
		self.STATUS_BAR_MSG.emit("Opening chapter {}".format(chap_numb+1))
		series = index.data(Qt.UserRole+1)
		utils.open(series.chapters[chap_numb])

	def contextMenuEvent(self, event):
		handled = False
		custom = False
		index = self.indexAt(event.pos())

		menu = QMenu()
		all_1 = QAction("Open First Chapter", menu,
				  triggered = lambda: self.open_chapter(index, 0))
		all_2 = QAction("Edit...", menu, triggered = lambda: self.spawn_dialog(index))
		all_3 = QAction("Remove", menu, triggered = lambda: self.remove_series(index))
		
		def fav():
			self.favourite(index)

		# add the chapter menus
		def chapters():
			menu.addSeparator()
			chapters_menu = QAction("Chapters", menu)
			menu.addAction(chapters_menu)
			open_chapters = QMenu()
			chapters_menu.setMenu(open_chapters)
			for number, chap_number in enumerate(range(len(
				index.data(Qt.UserRole+1).chapters)), 1):
				chap_action = QAction("Open chapter {}".format(
					number), open_chapters, triggered = lambda: self.open_chapter(index, chap_number))
				open_chapters.addAction(chap_action)

		if index.isValid():
			self.manga_delegate.CONTEXT_ON = True
			if index.data(Qt.UserRole+1).fav==1: # here you can limit which items to show these actions for
				action_1 = QAction("Favourite", menu, triggered = fav)
				action_1.setCheckable(True)
				action_1.setChecked(True)
				menu.addAction(action_1)
				chapters()
				handled = True
				custom = True
			if index.data(Qt.UserRole+1).fav==0: # here you can limit which items to show these actions for
				action_1 = QAction("Favourite", menu, triggered = fav)
				action_1.setCheckable(True)
				action_1.setChecked(False)
				menu.addAction(action_1)
				chapters()
				handled = True
				custom = True
		else:
			add_series = QAction("&Add new Series...", menu,
						triggered = self.SERIES_DIALOG.emit)
			menu.addAction(add_series)
			sort_main = QAction("&Sort by", menu)
			menu.addAction(sort_main)
			sort_menu = QMenu()
			sort_main.setMenu(sort_menu)
			asc_desc = QAction("Asc/Desc", menu, triggered = self.foo)
			s_title = QAction("Title", menu, triggered = self.foo)
			s_artist = QAction("Author", menu, triggered = self.foo)
			sort_menu.addAction(asc_desc)
			sort_menu.addSeparator()
			sort_menu.addAction(s_title)
			sort_menu.addAction(s_artist)
			refresh = QAction("&Refresh", menu,
					 triggered = self.model().layoutChanged.emit)
			menu.addAction(refresh)
			handled = True

		if handled and custom:
			menu.addSeparator()
			menu.addAction(all_1)
			menu.addAction(all_2)
			menu.addSeparator()
			menu.addAction(all_3)
			menu.exec_(event.globalPos())
			self.manga_delegate.CONTEXT_ON = False
			event.accept()
		elif handled:
			menu.exec_(event.globalPos())
			self.manga_delegate.CONTEXT_ON = False
			event.accept()
		else:
			event.ignore()

	#need this for debugging purposes
	def resizeEvent(self, resizeevent):
		super().resizeEvent(resizeevent)
		#print(resizeevent.size())

	def replace_edit_series(self, list_of_series, pos):
		"Replaces the view and DB with given list of series, at given position"
		assert isinstance(list_of_series, list), "Please pass a series to replace with"
		assert isinstance(pos, int)
		for series in list_of_series:

			kwdict = {'title':series.title,
			 'artist':series.artist,
			 'info':series.info,
			 'type':series.type,
			 'language':series.language,
			 'status':series.status,
			 'pub_date':series.pub_date,
			 'tags':series.tags}

			threading.Thread(target=seriesdb.SeriesDB.modify_series,
							 args=(series.id,), kwargs=kwdict).start()
		self.model().replaceRows([series], pos, len(list_of_series))

	def spawn_dialog(self, index=False):
		if not index:
			dialog = misc.SeriesDialog()
			dialog.SERIES.connect(self.series_model.addRows)
			dialog.trigger() # TODO: implement mass series' adding
		else:
			dialog = misc.SeriesDialog()
			dialog.SERIES_EDIT.connect(self.replace_edit_series)
			dialog.trigger([index])

	def updateGeometries(self):
		super().updateGeometries()
		self.verticalScrollBar().setSingleStep(gui_constants.SCROLL_SPEED)

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


if __name__ == '__main__':
	raise NotImplementedError("Unit testing not yet implemented")
