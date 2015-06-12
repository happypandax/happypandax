"""
This file is part of Happypanda.
Happypanda is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
any later version.
Happypanda is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with Happypanda.  If not, see <http://www.gnu.org/licenses/>.
"""

from PyQt5.QtCore import (Qt, QAbstractListModel, QModelIndex, QVariant,
						  QSize, QRect, QEvent, pyqtSignal, QThread,
						  QTimer, QPointF, QSortFilterProxyModel,
						  QAbstractTableModel, QItemSelectionModel)
from PyQt5.QtGui import (QPixmap, QBrush, QColor, QPainter, 
						 QPen, QTextDocument,
						 QMouseEvent, QHelpEvent,
						 QPixmapCache, QCursor, QPalette, QKeyEvent)
from PyQt5.QtWidgets import (QListView, QFrame, QLabel,
							 QStyledItemDelegate, QStyle,
							 QMenu, QAction, QToolTip, QVBoxLayout,
							 QSizePolicy, QTableWidget, QScrollArea,
							 QHBoxLayout, QFormLayout, QDesktopWidget,
							 QWidget, QHeaderView, QTableView, QApplication,
							 QRubberBand)
import threading
import re as regex
import logging

from ..database import seriesdb
from . import gui_constants, misc
from .. import utils

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical

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

		self.lang = QLabel()
		lang_lbl = QLabel("Language:")

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

		link_lbl = QLabel("Link:")
		self.link = QLabel()
		self.link.setWordWrap(True)

		form_l.addRow(self.title_lbl, self.title)
		form_l.addRow(self.artist_lbl, self.artist)
		form_l.addRow(self.chapters_lbl, self.chapters)
		form_l.addRow(self.info_lbl, self.info)
		form_l.addRow(lang_lbl, self.lang)
		form_l.addRow(self.tags_lbl, self.tags)
		form_l.addRow(link_lbl, self.link)

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
		self.lang.setText(series.language)
		self.type.setText(series.type)
		self.status.setText(series.status)
		self.tags.setText(tags_parser(series.tags))
		self.link.setText(series.link)

class SortFilterModel(QSortFilterProxyModel):
	def __init__(self, parent=None):
		super().__init__(parent)
		self._data = []

		# filtering
		self.fav = False
		self.tags = {}
		self.title = ""
		self.artist = ""

	def fav_view(self):
		self.fav = True
		self.invalidateFilter()

	def catalog_view(self):
		self.fav = False
		self.invalidateFilter()
	
	def change_model(self, model):
		self.setSourceModel(model)
		self._data = self.sourceModel()._data

	def populate_data(self):
		self.sourceModel().populate_data()

	def status_b_msg(self, msg):
		self.sourceModel().status_b_msg(msg)

	def addRows(self, list_of_series, position=None,
				rows=1, index = QModelIndex()):
		self.sourceModel().addRows(list_of_series, position, rows, index)

	def replaceRows(self, list_of_series, position, rows=1, index=QModelIndex()):
		self.sourceModel().replaceRows(list_of_series, position, rows, index)

	def search(self, term, title=True, artist=True, tags=True):
		"""
		Receives a search term.
		If title/artist/tags True: searches in it
		"""

		def f_tags():
			self.tags = utils.tag_to_dict(term)

		def f_title():
			self.title = term

		def f_artist():
			self.artist = term

		if title and artist and tags:
			f_tags()
			f_title()
			f_artist()

		self.invalidateFilter()

	def filterAcceptsRow(self, source_row, index_parent):
		allow = False
		series = None

		def do_search():
			l = {'title':False, 'artist':False, 'tags':False}
			if self.title:
				l['title'] = True
			if self.artist:
				l['artist'] = True
			if self.tags:
				try:
					a = self.tags['default']
					if a:
						l['tags'] = True
				except IndexError:
					l['tags'] = True
			
			for x in l:
				if l[x]:
					return l
			return None

		def return_searched(where):
			allow = False

			def re_search(a, b):
				"searches for a in b"
				m = regex.search("({})".format(a), b, regex.IGNORECASE)
				return m

			if where['title']:
				if re_search(self.title, series.title):
					allow = True
			if where['artist']:
				if re_search(self.artist, series.artist):
					allow = True
			if where['tags']:
				#print(self.tags)
				ser_tags = utils.tag_to_string(series.tags)
				for ns in self.tags:
					if ns == 'default':
						for tag in self.tags[ns]:
							if re_search(tag, ser_tags):
								#print(ser_tags)
								allow = True
					else:
						t = {ns:[]}
						for tag in self.tags[ns]:
							t[ns].append(tag)
						tags_string = utils.tag_to_string(t)
						#print(tags_string)
						if re_search(tags_string, ser_tags):
							allow = True

			return allow

		if self.sourceModel():
			index = self.sourceModel().index(source_row, 0, index_parent)
			if index.isValid():
				series = index.data(Qt.UserRole+1)
				if self.fav:
					if series.fav == 1:
						s = do_search()
						if s:
							allow = return_searched(s)
						else: allow = True
				else:
					s = do_search()
					if s:
						allow = return_searched(s)
					else: allow = True

		return allow

class SeriesModel(QAbstractTableModel):
	"""Model for Model/View/Delegate framework
	"""

	ROWCOUNT_CHANGE = pyqtSignal()
	STATUSBAR_MSG = pyqtSignal(str)
	CUSTOM_STATUS_MSG = pyqtSignal(str)
	_data = []

	def __init__(self, parent=None):
		super().__init__(parent)
		self._data_count = 0 # number of items added to model
		self.populate_data()
		#self._data_container = []
		self.dataChanged.connect(lambda: self.status_b_msg("Edited"))
		self.CUSTOM_STATUS_MSG.connect(self.status_b_msg)
		self._TITLE = gui_constants.TITLE
		self._ARTIST = gui_constants.ARTIST
		self._TAGS = gui_constants.TAGS
		self._TYPE = gui_constants.TYPE
		self._FAV = gui_constants.FAV
		self._CHAPTERS = gui_constants.CHAPTERS
		self._LANGUAGE = gui_constants.LANGUAGE
		self._LINK = gui_constants.LINK

	def populate_data(self):
		"Populates the model with data from database"
		self._data = seriesdb.SeriesDB.get_all_series()
		self.layoutChanged.emit()
		self.ROWCOUNT_CHANGE.emit()

	def status_b_msg(self, msg):
		self.STATUSBAR_MSG.emit(msg)

	def data(self, index, role=Qt.DisplayRole):
		if not index.isValid():
			return QVariant()
		if index.row() >= len(self._data) or \
			index.row() < 0:
			return QVariant()

		current_row = index.row() 
		current_series = self._data[current_row]
		current_column = index.column()

		def column_checker():
			if current_column == self._TITLE:
				title = current_series.title
				return title
			elif current_column == self._ARTIST:
				artist = current_series.artist
				return artist
			elif current_column == self._TAGS:
				tags = utils.tag_to_string(current_series.tags)
				return tags
			elif current_column == self._TYPE:
				type = current_series.type
				return type
			elif current_column == self._FAV:
				if current_series.fav == 1:
					return u'\u2605'
				else:
					return ''
			elif current_column == self._CHAPTERS:
				return len(current_series.chapters)
			elif current_column == self._LANGUAGE:
				return current_series.language
			elif current_column == self._LINK:
				return current_series.link

		if role == Qt.DisplayRole:
			return column_checker()
		# for artist searching
		if role == Qt.UserRole+2:
			artist = current_series.artist
			return artist

		if role == Qt.DecorationRole:
			pixmap = current_series.profile
			return pixmap
		
		if role == Qt.BackgroundRole:
			bg_color = QColor(242, 242, 242)
			bg_brush = QBrush(bg_color)
			return bg_brush

		if role == Qt.ToolTipRole:
			return column_checker()

		#if role == Qt.ToolTipRole:
		#	return "Example popup!!"
		if role == Qt.UserRole+1:
			return current_series

		# favourite satus
		if role == Qt.UserRole+3:
			return current_series.fav


		return None

	def rowCount(self, index = QModelIndex()):
		return self._data_count

	def columnCount(self, parent = QModelIndex()):
		return len(gui_constants.COLUMNS)

	def headerData(self, section, orientation, role = Qt.DisplayRole):
		if role == Qt.TextAlignmentRole:
			return Qt.AlignLeft
		if role != Qt.DisplayRole:
			return None
		if orientation == Qt.Horizontal:
			if section == self._TITLE:
				return 'Title'
			elif section == self._ARTIST:
				return 'Author'
			elif section == self._TAGS:
				return 'Tags'
			elif section == self._TYPE:
				return 'Type'
			elif section == self._FAV:
				return u'\u2605'
			elif section == self._CHAPTERS:
				return 'Chapters'
			elif section == self._LANGUAGE:
				return 'Language'
			elif section == self._LINK:
				return 'Link'
		return section + 1
	#def flags(self, index):
	#	if not index.isValid():
	#		return Qt.ItemIsEnabled
	#	return Qt.ItemFlags(QAbstractListModel.flags(self, index) |
	#				  Qt.ItemIsEditable)

	def addRows(self, list_of_series, position=None,
				rows=1, index = QModelIndex()):
		"Adds new series data to model and to DB"
		loading = misc.Loading(self.parent())
		loading.setText('Adding...')
		loading.progress.setMinimum(0)
		loading.progress.setMaximum(0)
		loading.show()
		from ..database.seriesdb import PROFILE_TO_MODEL
		if not position:
			position = len(self._data)
		self.beginInsertRows(QModelIndex(), position, position + rows - 1)
		for series in list_of_series:
			threading.Thread(target=seriesdb.SeriesDB.add_series_return, args=(series,)).start()
			series.profile = PROFILE_TO_MODEL.get()
			self._data.insert(0, series)
		self.endInsertRows()
		self.CUSTOM_STATUS_MSG.emit("Added item(s)")
		self.ROWCOUNT_CHANGE.emit()
		loading.close()
		return True

	def insertRows(self, list_of_series, position,
				rows=1, index = QModelIndex()):
		"Inserts new series data to the data list WITHOUT adding to DB"
		self.beginInsertRows(QModelIndex(), position, position + rows - 1)
		for pos, series in enumerate(list_of_series, 1):
			self._data.append(series)
		self.endInsertRows()
		self.CUSTOM_STATUS_MSG.emit("Added item(s)")
		self.ROWCOUNT_CHANGE.emit()
		return True

	def replaceRows(self, list_of_series, position, rows=1, index=QModelIndex()):
		"replaces series data to the data list WITHOUT adding to DB"
		for pos, series in enumerate(list_of_series):
			del self._data[position+pos]
			self._data.insert(position+pos, series)
		self.dataChanged.emit(index, index, [Qt.UserRole+1])

	def removeRows(self, position, rows=1, index=QModelIndex()):
		"Deletes series data from the model data list. OBS: doesn't touch DB!"
		self.beginRemoveRows(QModelIndex(), position, position + rows - 1)
		self._data = self._data[:position] + self._data[position + rows:]
		self._data_count -= rows
		self.endRemoveRows()
		self.ROWCOUNT_CHANGE.emit()
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
			r = option.rect.adjusted(1, -2, -1, 0)
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
				painter.drawPixmap(QRect(x, y, w, self.image.height()),
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
			if option.state & QStyle.State_Selected:
				painter.fillRect(option.rect, QColor(164,164,164,120))

			#if option.state & QStyle.State_Selected:
			#	painter.setPen(QPen(option.palette.highlightedText().color()))
		else:
			super().paint(painter, option, index)

	def sizeHint(self, QStyleOptionViewItem, QModelIndex):
		return QSize(self.W, self.H)

# TODO: Redo this part to avoid duplicated code




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
		self.setSelectionBehavior(self.SelectItems)
		self.setSelectionMode(self.ExtendedSelection)
		# improve scrolling
		self.setVerticalScrollMode(self.ScrollPerPixel)
		self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		# prevent all items being loaded at the same time
		self.setLayoutMode(self.Batched)
		self.setBatchSize(gui_constants.PREFETCH_ITEM_AMOUNT)
		self.setMouseTracking(True)
		self.sort_model = SortFilterModel()
		self.sort_model.setDynamicSortFilter(True)
		self.sort_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
		self.sort_model.setSortLocaleAware(True)
		self.sort_model.setSortCaseSensitivity(Qt.CaseInsensitive)
		self.manga_delegate = CustomDelegate()
		self.setItemDelegate(self.manga_delegate)
		self.series_model = SeriesModel(parent)
		self.sort_model.change_model(self.series_model)
		self.sort_model.sort(0)
		self.setModel(self.sort_model)
		self.SERIES_DIALOG.connect(self.spawn_dialog)
		self.doubleClicked.connect(self.open_chapter)

	def remove_series(self, index_list):
		for index in index_list:
			self.rowsAboutToBeRemoved(index.parent(), index.row(), index.row())
			series = index.data(Qt.UserRole+1)
			self.series_model.removeRows(index.row(), 1)
			threading.Thread(target=seriesdb.SeriesDB.del_series,
					   args=(series.id,), daemon=True).start()

	def favourite(self, index):
		assert isinstance(index, QModelIndex)
		series = index.data(Qt.UserRole+1)
		# TODO: don't need to fetch from DB here... 
		if series.fav == 1:
			n_series = seriesdb.SeriesDB.fav_series_set(series.id, 0)
			self.model().replaceRows([n_series], index.row(), 1, index)
			self.series_model.CUSTOM_STATUS_MSG.emit("Unfavourited")
		else:
			n_series = seriesdb.SeriesDB.fav_series_set(series.id, 1)
			self.model().replaceRows([n_series], index.row(), 1, index)
			self.series_model.CUSTOM_STATUS_MSG.emit("Favourited")

	def open_chapter(self, index, chap_numb=0):
		if isinstance(index, list):
			for x in index:
				series = x.data(Qt.UserRole+1)
				self.STATUS_BAR_MSG.emit("Opening chapters of selected series'")
				threading.Thread(target=utils.open,
						   args=(series.chapters[chap_numb],)).start()
		else:
			series = index.data(Qt.UserRole+1)
			self.STATUS_BAR_MSG.emit("Opening chapter {} of {}".format(chap_numb+1,
																 series.title))
			threading.Thread(target=utils.open,
					   args=(series.chapters[chap_numb],)).start()

	def refresh(self):
		self.model().populate_data()
		self.STATUS_BAR_MSG.emit("Refreshed")

	def contextMenuEvent(self, event):
		handled = False
		custom = False
		index = self.indexAt(event.pos())
		index = self.sort_model.mapToSource(index)

		selected = False
		select_indexes = self.selectedIndexes()
		if len(select_indexes) > 1:
			selected = True

		menu = QMenu()
		if selected:
			all_0 = QAction("Open first chapters", menu,
					  triggered = lambda: self.open_chapter(select_indexes, 0))
			all_4 = QAction("Remove selected", menu,
				   triggered = lambda: self.remove_series(select_indexes))
		all_1 = QAction("Open first chapter", menu,
					triggered = lambda: self.open_chapter(index, 0))
		all_2 = QAction("Edit...", menu, triggered = lambda: self.spawn_dialog(index))
		all_3 = QAction("Remove", menu, triggered = lambda: self.remove_series([index]))
		
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

		def open_link():
			link = index.data(Qt.UserRole+1).link
			utils.open_web_link(link)

		def sort_title():
			self.sort_model.setSortRole(Qt.DisplayRole)
			self.sort_model.sort(0, Qt.AscendingOrder)

		def sort_artist():
			self.sort_model.setSortRole(Qt.UserRole+2)
			self.sort_model.sort(0, Qt.AscendingOrder)

		def asc_desc():
			if self.sort_model.sortOrder() == Qt.AscendingOrder:
				self.sort_model.sort(0, Qt.DescendingOrder)
			else:
				self.sort_model.sort(0, Qt.AscendingOrder)


		if index.isValid():
			self.manga_delegate.CONTEXT_ON = True

			if index.data(Qt.UserRole+1).link != "":
				ext_action = QAction("Open link", menu, triggered = open_link)

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
			asc_desc = QAction("Asc/Desc", menu,
					  triggered = asc_desc)
			s_title = QAction("Title", menu,
					 triggered = sort_title)
			s_artist = QAction("Author", menu,
					  triggered = sort_artist)
			s_date = QAction("Date Added", menu)
			sort_menu.addAction(asc_desc)
			sort_menu.addSeparator()
			sort_menu.addAction(s_title)
			sort_menu.addAction(s_artist)
			sort_menu.addAction(s_date)
			refresh = QAction("&Refresh", menu,
					 triggered = self.refresh)
			menu.addAction(refresh)
			handled = True

		if handled and custom:
			menu.addSeparator()
			try:
				menu.addAction(all_0)
			except:
				pass
			menu.addAction(all_1)
			menu.addAction(all_2)
			try:
				menu.addAction(ext_action)
			except:
				pass
			menu.addSeparator()
			menu.addAction(all_3)
			try:
				menu.addAction(all_4)
			except:
				pass
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
			 'tags':series.tags,
			 'link':series.link}

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

class MangaTableView(QTableView):
	STATUS_BAR_MSG = pyqtSignal(str)
	SERIES_DIALOG = pyqtSignal()

	def __init__(self, parent=None):
		super().__init__(parent)
		# options
		self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
		self.setSelectionBehavior(self.SelectRows)
		self.setSelectionMode(self.ExtendedSelection)
		self.setShowGrid(True)
		self.setSortingEnabled(True)
		v_header = self.verticalHeader()
		v_header.sectionResizeMode(QHeaderView.Fixed)
		v_header.setDefaultSectionSize(24)
		v_header.hide()
		palette = self.palette()
		palette.setColor(palette.Highlight, QColor(88, 88, 88, 70))
		palette.setColor(palette.HighlightedText, QColor('black'))
		self.setPalette(palette)
		self.setIconSize(QSize(0,0))
		self.doubleClicked.connect(self.open_chapter)

	def viewportEvent(self, event):
		if event.type() == QEvent.ToolTip:
			h_event = QHelpEvent(event)
			index = self.indexAt(h_event.pos())
			if index.isValid():
				size_hint = self.itemDelegate(index).sizeHint(self.viewOptions(),
												  index)
				rect = QRect(0, 0, size_hint.width(), size_hint.height())
				rect_visual = self.visualRect(index)
				if rect.width() <= rect_visual.width():
					QToolTip.hideText()
					return True
		return super().viewportEvent(event)

	def remove_series(self, index):
		self.rowsAboutToBeRemoved(index.parent(), index.row(), index.row())
		series = index.data(Qt.UserRole+1)
		self.series_model.removeRows(index.row(), 1)
		threading.Thread(target=seriesdb.SeriesDB.del_series,
				   args=(series.id,), daemon=True).start()

	def favourite(self, index):
		assert isinstance(index, QModelIndex)
		series = index.data(Qt.UserRole+1)
		# TODO: don't need to fetch from DB here... 
		if series.fav == 1:
			n_series = seriesdb.SeriesDB.fav_series_set(series.id, 0)
			self.model().replaceRows([n_series], index.row(), 1, index)
			self.series_model.CUSTOM_STATUS_MSG.emit("Unfavourited")
		else:
			n_series = seriesdb.SeriesDB.fav_series_set(series.id, 1)
			self.model().replaceRows([n_series], index.row(), 1, index)
			self.series_model.CUSTOM_STATUS_MSG.emit("Favourited")

	def open_chapter(self, index, chap_numb=0):
		series = index.data(Qt.UserRole+1)
		self.STATUS_BAR_MSG.emit("Opening chapter {} of {}".format(chap_numb+1,
															 series.title))
		threading.Thread(target=utils.open,
				   args=(series.chapters[chap_numb],)).start()

	def refresh(self):
		self.model().populate_data()
		self.STATUS_BAR_MSG.emit("Refreshed")

	def contextMenuEvent(self, event):
		handled = False
		custom = False
		index = self.indexAt(event.pos())
		index = self.sort_model.mapToSource(index)

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

		def open_link():
			link = index.data(Qt.UserRole+1).link
			utils.open_web_link(link)

		def sort_title():
			self.sort_model.setSortRole(Qt.DisplayRole)
			self.sort_model.sort(0, Qt.AscendingOrder)

		def sort_artist():
			self.sort_model.setSortRole(Qt.UserRole+2)
			self.sort_model.sort(0, Qt.AscendingOrder)

		def asc_desc():
			if self.sort_model.sortOrder() == Qt.AscendingOrder:
				self.sort_model.sort(0, Qt.DescendingOrder)
			else:
				self.sort_model.sort(0, Qt.AscendingOrder)


		if index.isValid():
			if index.data(Qt.UserRole+1).link != "":
				ext_action = QAction("Open link", menu, triggered = open_link)

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
			asc_desc = QAction("Asc/Desc", menu,
					  triggered = asc_desc)
			s_title = QAction("Title", menu,
					 triggered = sort_title)
			s_artist = QAction("Author", menu,
					  triggered = sort_artist)
			sort_menu.addAction(asc_desc)
			sort_menu.addSeparator()
			sort_menu.addAction(s_title)
			sort_menu.addAction(s_artist)
			refresh = QAction("&Refresh", menu,
					 triggered = self.refresh)
			menu.addAction(refresh)
			handled = True

		if handled and custom:
			menu.addSeparator()
			menu.addAction(all_1)
			menu.addAction(all_2)
			try:
				menu.addAction(ext_action)
			except:
				pass
			menu.addSeparator()
			menu.addAction(all_3)
			menu.exec_(event.globalPos())
			event.accept()
		elif handled:
			menu.exec_(event.globalPos())
			event.accept()
		else:
			event.ignore()

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
			 'tags':series.tags,
			 'link':series.link}

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

if __name__ == '__main__':
	raise NotImplementedError("Unit testing not yet implemented")
