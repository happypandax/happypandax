#"""
#This file is part of Happypanda.
#Happypanda is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 2 of the License, or
#any later version.
#Happypanda is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#You should have received a copy of the GNU General Public License
#along with Happypanda.  If not, see <http://www.gnu.org/licenses/>.
#"""

import threading, logging, os, math, functools, random
import re as regex

from PyQt5.QtCore import (Qt, QAbstractListModel, QModelIndex, QVariant,
						  QSize, QRect, QEvent, pyqtSignal, QThread,
						  QTimer, QPointF, QSortFilterProxyModel,
						  QAbstractTableModel, QItemSelectionModel,
						  QPoint, QRectF, QDate, QDateTime)
from PyQt5.QtGui import (QPixmap, QBrush, QColor, QPainter, 
						 QPen, QTextDocument,
						 QMouseEvent, QHelpEvent,
						 QPixmapCache, QCursor, QPalette, QKeyEvent,
						 QFont, QTextOption, QFontMetrics, QFontMetricsF,
						 QTextLayout)
from PyQt5.QtWidgets import (QListView, QFrame, QLabel,
							 QStyledItemDelegate, QStyle,
							 QMenu, QAction, QToolTip, QVBoxLayout,
							 QSizePolicy, QTableWidget, QScrollArea,
							 QHBoxLayout, QFormLayout, QDesktopWidget,
							 QWidget, QHeaderView, QTableView, QApplication,
							 QMessageBox, QActionGroup)

import gallerydb
import gui_constants
import misc
import gallerydialog
import file_misc
import utils

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical

class Popup(QWidget):
	def __init__(self, parent=None):
		super().__init__(parent, Qt.Window | Qt.FramelessWindowHint)
		self.setAttribute(Qt.WA_ShowWithoutActivating)
		self.initUI()
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

	def set_gallery(self, gallery):
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
		self.title.setText(gallery.title)
		self.artist.setText(gallery.artist)
		self.chapters.setText("{}".format(len(gallery.chapters)))
		self.info.setText(gallery.info)
		self.lang.setText(gallery.language)
		self.type.setText(gallery.type)
		self.status.setText(gallery.status)
		self.tags.setText(tags_parser(gallery.tags))
		self.link.setText(gallery.link)

class SortFilterModel(QSortFilterProxyModel):
	ROWCOUNT_CHANGE = pyqtSignal()
	def __init__(self, parent=None):
		super().__init__(parent)
		self._data = []

		# filtering
		self.fav = False
		self.tags = {}
		self.title = ""
		self.artist = ""
		self.allow_all = True
		self.excludes = []

	def fav_view(self):
		self.fav = True
		self.invalidateFilter()
		self.ROWCOUNT_CHANGE.emit()

	def catalog_view(self):
		self.fav = False
		self.invalidateFilter()
		self.ROWCOUNT_CHANGE.emit()
	
	def change_model(self, model):
		self.setSourceModel(model)
		self._data = self.sourceModel()._data

	def populate_data(self):
		self.sourceModel().populate_data()

	def status_b_msg(self, msg):
		self.sourceModel().status_b_msg(msg)

	def addRows(self, list_of_gallery, position=None,
				rows=1, index = QModelIndex()):
		self.sourceModel().addRows(list_of_gallery, position, rows, index)

	def replaceRows(self, list_of_gallery, position, rows=1, index=QModelIndex()):
		self.sourceModel().replaceRows(list_of_gallery, position, rows, index)

	def search(self, term, title=True, artist=True, tags=True):
		"""
		Receives a search term.
		If title/artist/tags True: searches in them
		"""
		self.excludes = []
		def trim_for_non_tag(txt):
			level = 0 # so we know if we are in a list
			buffer = ""
			stripped_set = set() # we only need unique values
			for n, x in enumerate(txt, 1):

				if x == '[':
					level += 1 # we are now entering a list
				if x == ']':
					level -= 1 # we are now exiting a list


				if x == ',': # if we meet a comma
					# we trim our buffer if we are at top level
					if level is 0:
						# add to list
						stripped_set.add(buffer.strip())
						buffer = ""
					else:
						buffer += x
				elif n == len(txt): # or at end of string
					buffer += x
					# add to list
					stripped_set.add(buffer.strip())
					buffer = ""
				else:
					buffer += x
			for s in stripped_set:
				if not ':' in s:
					txt = s
			txt = txt.split(' ')
			txt = [x.strip() for x in txt]
			return txt

		if len(term) > 0:
			self.allow_all = False
			if title:
				if 'title:' in term:
					t = regex.search('(?<=title:)"([^"]*)"', term)
					if t:
						n = t.group()
						term = term.replace('title:'+n, '')
						t = n.replace('"', '')
						self.title = [t]
				else:
					self.title = trim_for_non_tag(term)

			if artist:
				if 'artist:' in term:
					a = regex.search('(?<=artist:)"([^"]*)"', term)
					if a:
						n = a.group()
						term = term.replace('artist:'+n, '')
						a = n.replace('"', '')
						self.artist = a
				elif 'author:' in term:
					a = regex.search('(?<=author:)"([^"]*)"', term)
					if a:
						n = a.group()
						term = term.replace('author:'+n, '')
						a = n.replace('"', '')
						self.artist = a
				else:
					self.artist = trim_for_non_tag(term)

			if tags:
				self.tags = utils.tag_to_dict(term)
		else:
			self.allow_all = True

		self.invalidateFilter()
		self.ROWCOUNT_CHANGE.emit()

	def filterAcceptsRow(self, source_row, index_parent):
		allow = False
		gallery = None

		def do_search():
			l = {'title':False, 'artist':False, 'tags':False}
			if self.title:
				l['title'] = True
			if self.artist:
				l['artist'] = True
			if self.tags:
				l['tags'] = True
			
			return l

		def return_searched(where):
			allow = False

			def re_search(a, b):
				"searches for a in b"
				try:
					m = regex.search("({})".format(a), b, regex.IGNORECASE)
				except regex.error:
					return None
				return m

			if where['tags']:
				tag_allow = []
				ser_tags = gallery.tags
				for ns in self.tags:
					if ns == 'default':
						if ns in ser_tags:
							for tag in self.tags[ns]:
								if tag in ser_tags[ns]:
									tag_allow.append(True)
								else:
									tag_allow.append(False)
									#print(self.tags)
						else: continue
					else:
						if ns in ser_tags:
							for tag in self.tags[ns]:
								if tag in ser_tags[ns]:
									tag_allow.append(True)
								else:
									tag_allow.append(False)
								#print(self.tags)
						else:
							tag_allow.append(False)
				if len(tag_allow) != 0 and all(tag_allow):
					allow = True
			if where['title']:
				title_allow = []
				#print(self.title)
				if all(self.title):
					for t in self.title:
						if re_search(t, gallery.title):
							title_allow.append(True)
						else:
							title_allow.append(False)
					if len(title_allow) > 0 and all(title_allow):
						allow = True
			if where['artist']:
				artist_allow = []
				#print(self.artist)
				if all(self.artist):
					for a in self.artist:
						if re_search(a, gallery.artist):
							artist_allow.append(True)
						else:
							artist_allow.append(False)
					if len(artist_allow) > 0 and all(artist_allow):
						allow = True

			return allow

		if self.sourceModel():
			index = self.sourceModel().index(source_row, 0, index_parent)
			if index.isValid():
				gallery = index.data(Qt.UserRole+1)
				if self.fav:
					if gallery.fav == 1:
						s = do_search()
						if s:
							allow = return_searched(s)
						else: allow = True
						if self.allow_all:
							return True
				else:
					s = do_search()
					if s:
						allow = return_searched(s)
					else: allow = True
					if self.allow_all:
						return True
		return allow

class GalleryModel(QAbstractTableModel):
	"""Model for Model/View/Delegate framework
	"""

	ROWCOUNT_CHANGE = pyqtSignal()
	STATUSBAR_MSG = pyqtSignal(str)
	CUSTOM_STATUS_MSG = pyqtSignal(str)
	_data = []

	def __init__(self, parent=None):
		super().__init__(parent)
		self._data_count = 0 # number of items added to model
		#self.populate_data()
		#self._data_container = []
		self.dataChanged.connect(lambda: self.status_b_msg("Edited"))
		self.dataChanged.connect(lambda: self.ROWCOUNT_CHANGE.emit())
		self.layoutChanged.connect(lambda: self.ROWCOUNT_CHANGE.emit())
		self.CUSTOM_STATUS_MSG.connect(self.status_b_msg)
		self._TITLE = gui_constants.TITLE
		self._ARTIST = gui_constants.ARTIST
		self._TAGS = gui_constants.TAGS
		self._TYPE = gui_constants.TYPE
		self._FAV = gui_constants.FAV
		self._CHAPTERS = gui_constants.CHAPTERS
		self._LANGUAGE = gui_constants.LANGUAGE
		self._LINK = gui_constants.LINK
		self._DESCR = gui_constants.DESCR
		self._DATE_ADDED = gui_constants.DATE_ADDED
		self._PUB_DATE = gui_constants.PUB_DATE

	def init_data(self):
		"Populates the model with data from database"
		self._data = []
		for gallery in gallerydb.GalleryDB.get_all_gallery():
			if not gallery.valid:
				reasons = gallery.invalidities()
			else:
				self._data.append(gallery)
		self._data_count = len(self._data)
		self.layoutChanged.emit()
		self.ROWCOUNT_CHANGE.emit()

	def populate_data(self):
		"Populates the model with data from database in a timely manner"
		self._data = []
		t = 0
		galleries = gallerydb.GalleryDB.get_all_gallery()
		self._data_count = len(galleries)
		for pos, gallery in enumerate(galleries):
			t += 80
			if not gallery.valid:
				reasons = gallery.invalidities()
			else:
				QTimer.singleShot(t, functools.partial(self.insertRows, [gallery], pos,
										   data_count=False))

	def status_b_msg(self, msg):
		self.STATUSBAR_MSG.emit(msg)

	def data(self, index, role=Qt.DisplayRole):
		if not index.isValid():
			return QVariant()
		if index.row() >= len(self._data) or \
			index.row() < 0:
			return QVariant()

		current_row = index.row() 
		current_gallery = self._data[current_row]
		current_column = index.column()

		def column_checker():
			if current_column == self._TITLE:
				title = current_gallery.title
				return title
			elif current_column == self._ARTIST:
				artist = current_gallery.artist
				return artist
			elif current_column == self._TAGS:
				tags = utils.tag_to_string(current_gallery.tags)
				return tags
			elif current_column == self._TYPE:
				type = current_gallery.type
				return type
			elif current_column == self._FAV:
				if current_gallery.fav == 1:
					return u'\u2605'
				else:
					return ''
			elif current_column == self._CHAPTERS:
				return len(current_gallery.chapters)
			elif current_column == self._LANGUAGE:
				return current_gallery.language
			elif current_column == self._LINK:
				return current_gallery.link
			elif current_column == self._DESCR:
				return current_gallery.info
			elif current_column == self._DATE_ADDED:
				g_dt = "{}".format(current_gallery.date_added)
				qdate_g_dt = QDateTime.fromString(g_dt, "yyyy-MM-dd HH:mm:ss")
				return qdate_g_dt
			elif current_column == self._PUB_DATE:
				g_pdt = "{}".format(current_gallery.pub_date)
				qdate_g_pdt = QDateTime.fromString(g_pdt, "yyyy-MM-dd HH:mm:ss")
				if qdate_g_pdt.isValid():
					return qdate_g_pdt
				else:
					'No date set'

		# TODO: name all these roles and put them in gui_constants...

		if role == Qt.DisplayRole:
			return column_checker()
		# for artist searching
		if role == Qt.UserRole+2:
			artist = current_gallery.artist
			return artist

		if role == Qt.DecorationRole:
			pixmap = current_gallery.profile
			return pixmap
		
		if role == Qt.BackgroundRole:
			bg_color = QColor(242, 242, 242)
			bg_brush = QBrush(bg_color)
			return bg_brush

		if gui_constants.GRID_TOOLTIP and role == Qt.ToolTipRole:
			add_bold = []
			add_tips = []
			if gui_constants.TOOLTIP_TITLE:
				add_bold.append('<b>Title:</b>')
				add_tips.append(current_gallery.title)
			if gui_constants.TOOLTIP_AUTHOR:
				add_bold.append('<b>Author:</b>')
				add_tips.append(current_gallery.artist)
			if gui_constants.TOOLTIP_CHAPTERS:
				add_bold.append('<b>Chapters:</b>')
				add_tips.append(len(current_gallery.chapters))
			if gui_constants.TOOLTIP_STATUS:
				add_bold.append('<b>Status:</b>')
				add_tips.append(current_gallery.status)
			if gui_constants.TOOLTIP_TYPE:
				add_bold.append('<b>Type:</b>')
				add_tips.append(current_gallery.type)
			if gui_constants.TOOLTIP_LANG:
				add_bold.append('<b>Language:</b>')
				add_tips.append(current_gallery.language)
			if gui_constants.TOOLTIP_DESCR:
				add_bold.append('<b>Description:</b><br />')
				add_tips.append(current_gallery.info)
			if gui_constants.TOOLTIP_TAGS:
				add_bold.append('<b>Tags:</b>')
				add_tips.append(utils.tag_to_string(
					current_gallery.tags))
			if gui_constants.TOOLTIP_LAST_READ:
				add_bold.append('<b>Last read:</b>')
				add_tips.append(current_gallery.last_read)
			if gui_constants.TOOLTIP_TIMES_READ:
				add_bold.append('<b>Times read:</b>')
				add_tips.append(current_gallery.times_read)
			if gui_constants.TOOLTIP_PUB_DATE:
				add_bold.append('<b>Publication Date:</b>')
				add_tips.append('{}'.format(current_gallery.pub_date).split(' ')[0])
			if gui_constants.TOOLTIP_DATE_ADDED:
				add_bold.append('<b>Date added:</b>')
				add_tips.append('{}'.format(current_gallery.date_added).split(' ')[0])

			tooltip = ""
			tips = list(zip(add_bold, add_tips))
			for tip in tips:
				tooltip += "{} {}<br />".format(tip[0], tip[1])
			return tooltip

		if role == Qt.UserRole+1:
			return current_gallery

		# favorite satus
		if role == Qt.UserRole+3:
			return current_gallery.fav

		if role == Qt.UserRole+4:
			date_added = "{}".format(current_gallery.date_added)
			qdate_added = QDateTime.fromString(date_added, "yyyy-MM-dd HH:mm:ss")
			return qdate_added
		
		if role == Qt.UserRole+5:
			if current_gallery.pub_date:
				pub_date = "{}".format(current_gallery.pub_date)
				qpub_date = QDateTime.fromString(pub_date, "yyyy-MM-dd HH:mm:ss")
				return qpub_date

		return None

	def rowCount(self, index = QModelIndex()):
		return len(self._data)

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
			elif section == self._DESCR:
				return 'Description'
			elif section == self._DATE_ADDED:
				return 'Date Added'
			elif section == self._PUB_DATE:
				return 'Published'
		return section + 1
	#def flags(self, index):
	#	if not index.isValid():
	#		return Qt.ItemIsEnabled
	#	return Qt.ItemFlags(QAbstractListModel.flags(self, index) |
	#				  Qt.ItemIsEditable)

	def addRows(self, list_of_gallery, position=None,
				rows=1, index = QModelIndex()):
		"Adds new gallery data to model and to DB"
		log_d('Adding {} rows'.format(rows))
		if not position:
			log_d('Add rows: No position specified')
			position = len(self._data)
		self.beginInsertRows(QModelIndex(), position, position + rows - 1)
		log_d('Add rows: Began inserting')
		for gallery in list_of_gallery:
			gallerydb.add_method_queue(gallerydb.GalleryDB.add_gallery_return, True, gallery)
			gallery.profile = gallerydb.PROFILE_TO_MODEL.get()
			self._data.insert(position, gallery)
			self._data_count += 1
		log_d('Add rows: Finished inserting')
		self.endInsertRows()
		self.CUSTOM_STATUS_MSG.emit("Added item(s)")
		self.ROWCOUNT_CHANGE.emit()
		return True

	def insertRows(self, list_of_gallery, position=None,
				rows=1, index = QModelIndex(), data_count=True):
		"Inserts new gallery data to the data list WITHOUT adding to DB"
		position = len(self._data) if not position else position
		self.beginInsertRows(QModelIndex(), position, position + rows - 1)
		for pos, gallery in enumerate(list_of_gallery, 1):
			self._data.append(gallery)
			if data_count:
				self._data_count += 1
		self.endInsertRows()
		if data_count:
			self.CUSTOM_STATUS_MSG.emit("Added item(s)")
		self.ROWCOUNT_CHANGE.emit()
		return True

	def replaceRows(self, list_of_gallery, position, rows=1, index=QModelIndex()):
		"replaces gallery data to the data list WITHOUT adding to DB"
		for pos, gallery in enumerate(list_of_gallery):
			del self._data[position+pos]
			self._data.insert(position+pos, gallery)
		self.dataChanged.emit(index, index, [Qt.UserRole+1, Qt.DecorationRole])

	def removeRows(self, position, rows=1, index=QModelIndex()):
		"Deletes gallery data from the model data list. OBS: doesn't touch DB!"
		self.beginRemoveRows(QModelIndex(), position, position + rows - 1)
		self._data = self._data[:position] + self._data[position + rows:]
		self._data_count -= rows
		self.endRemoveRows()
		self.ROWCOUNT_CHANGE.emit()
		return True

	#def canFetchMore(self, index):
	#	if self._data_count < len(self._data):
	#		return True
	#	else: 
	#		return False

	#def fetchMore(self, index):
	#	print('Fetching more')
	#	diff = len(self._data) - self._data_count
	#	item_to_fetch = min(gui_constants.PREFETCH_ITEM_AMOUNT, diff)

	#	self.beginInsertRows(index, self._data_count,
	#				   self._data_count+item_to_fetch-1)
	#	self._data_count += item_to_fetch
	#	self.endInsertRows()
	#	self.ROWCOUNT_CHANGE.emit()

class CustomDelegate(QStyledItemDelegate):
	"A custom delegate for the model/view framework"

	POPUP = pyqtSignal()
	CONTEXT_ON = False

	def __init__(self, parent=None):
		super().__init__()
		QPixmapCache.setCacheLimit(gui_constants.THUMBNAIL_CACHE_SIZE[0]*
							 gui_constants.THUMBNAIL_CACHE_SIZE[1])
		self.popup_window = Popup(parent)
		self.popup_timer = QTimer()
		self._painted_indexes = {}

		misc.FileIcon.refresh_default_icon()
		self.font_size = gui_constants.GALLERY_FONT[1]
		self.font_name = gui_constants.GALLERY_FONT[0]
		if not self.font_name:
			self.font_name = QWidget().font().family()
		self.title_font = QFont()
		self.title_font.setBold(True)
		self.title_font.setFamily(self.font_name)
		self.artist_font = QFont()
		self.artist_font.setFamily(self.font_name)
		if self.font_size is not 0:
			self.title_font.setPixelSize(self.font_size)
			self.artist_font.setPixelSize(self.font_size)
		self.title_font_m = QFontMetrics(self.title_font)
		self.artist_font_m = QFontMetrics(self.artist_font)
		t_h = self.title_font_m.height()
		a_h = self.artist_font_m.height()
		self.text_label_h = a_h + t_h * 2
		self.W = gui_constants.THUMB_W_SIZE
		self.H = gui_constants.THUMB_H_SIZE + gui_constants.GRIDBOX_LBL_H#self.text_label_h #+ gui_constants.GRIDBOX_LBL_H
		#self.popup_timer.timeout.connect(self.POPUP.emit)

	def key(self, key):
		"Assigns an unique key to indexes"
		if key in self._painted_indexes:
			return self._painted_indexes[key]
		else:
			k = hash(key)
			self._painted_indexes[key] = str(k)
			return str(k)

	def paint(self, painter, option, index):
		#self.initStyleOption(option, index)

		assert isinstance(painter, QPainter)
		if index.data(Qt.UserRole+1):
			if gui_constants.HIGH_QUALITY_THUMBS:
				painter.setRenderHint(QPainter.SmoothPixmapTransform)
			painter.setRenderHint(QPainter.Antialiasing)
			gallery = index.data(Qt.UserRole+1)
			title = gallery.title
			artist = gallery.artist
			title_color = gui_constants.GRID_VIEW_TITLE_COLOR
			artist_color = gui_constants.GRID_VIEW_ARTIST_COLOR
			label_color = gui_constants.GRID_VIEW_LABEL_COLOR
			# Enable this to see the defining box
			#painter.drawRect(option.rect)
			# define font size
			if 20 > len(title) > 15:
				title_size = "font-size:{}px;".format(self.font_size)
			elif 30 > len(title) > 20:
				title_size = "font-size:{}px;".format(self.font_size-1)
			elif 40 > len(title) >= 30:
				title_size = "font-size:{}px;".format(self.font_size-2)
			elif 50 > len(title) >= 40:
				title_size = "font-size:{}px;".format(self.font_size-3)
			elif len(title) >= 50:
				title_size = "font-size:{}px;".format(self.font_size-4)
			else:
				title_size = "font-size:{}px;".format(self.font_size)

			if 30 > len(artist) > 20:
				artist_size = "font-size:{}px;".format(self.font_size)
			elif 40 > len(artist) >= 30:
				artist_size = "font-size:{}px;".format(self.font_size-1)
			elif len(artist) >= 40:
				artist_size = "font-size:{}px;".format(self.font_size-2)
			else:
				artist_size = "font-size:{}px;".format(self.font_size)

			#painter.setPen(QPen(Qt.NoPen))
			#option.rect = option.rect.adjusted(11, 10, 0, 0)
			option.rect.setWidth(self.W)

			option.rect.setHeight(self.H)
			rec = option.rect.getRect()
			x = rec[0]
			y = rec[1]
			w = rec[2]
			h = rec[3]

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
			color: {4};
			font-weight:bold;
			{0}
			}}
			#artist {{
			position:absolute;
			color: {5};
			top:20px;
			right:0;
			{1}
			}}
			</style>
			</head>
			<body>
			<div id="area">
			<center>
			<div id="title">{2}
			</div>
			<div id="artist">{3}
			</div>
			</div>
			</center>
			</body>
			""".format(title_size, artist_size, title, artist, title_color, artist_color))
			text_area.setTextWidth(w)

			#chapter_area = QTextDocument()
			#chapter_area.setDefaultFont(option.font)
			#chapter_area.setHtml("""
			#<font color="black">{}</font>
			#""".format("chapter"))
			#chapter_area.setTextWidth(w)

			# if we can't find a cached image
			pix_cache = QPixmapCache.find(self.key(gallery.profile))
			if isinstance(pix_cache, QPixmap):
				print('from cache')
				self.image = pix_cache
				if self.image.height() < self.image.width(): #to keep aspect ratio
					painter.drawPixmap(QPoint(x,y),
							self.image)
				else:
					painter.drawPixmap(QPoint(x,y),
							self.image)
			else:
				print('not from cache')
				self.image = QPixmap(gallery.profile)
				QPixmapCache.insert(self.key(gallery.profile), self.image)
				if self.image.height() < self.image.width(): #to keep aspect ratio
					painter.drawPixmap(QPoint(x,y),
							self.image)
				else:
					painter.drawPixmap(QPoint(x,y),
							self.image)

			# draw star if it's favorited
			if gallery.fav == 1:
				painter.drawPixmap(QPointF(x,y), QPixmap(gui_constants.STAR_PATH))
			
			# WARNING: CAUSE OF MEMORY LEAK!!
			#if gui_constants.REFRESH_GALLERY_ICONS:
			#	pass

			#if gui_constants.DISPLAY_GALLERY_TYPE:
			#	icon = misc.FileIcon.get_file_icon(gallery.path)
			#	if not icon.isNull():
			#		icon.paint(painter, QRect(x+2, y+gui_constants.THUMB_H_SIZE-16, 16, 16))

			#if gui_constants.USE_EXTERNAL_PROG_ICO:
			#	if gui_constants.USE_EXTERNAL_VIEWER:
			#		icon = misc.FileIcon.get_external_file_icon()
			#	else:
			#		icon = misc.FileIcon.get_default_file_icon()

			#	if icon:
			#		icon.paint(painter, QRect(x+w-30, y+gui_constants.THUMB_H_SIZE-28, 28, 28))
			def draw_text_label(lbl_h):
				#draw the label for text
				painter.save()
				painter.translate(x, y+gui_constants.THUMB_H_SIZE)
				box_color = QBrush(QColor(label_color))#QColor(0,0,0,123))
				painter.setBrush(box_color)
				rect = QRect(0, 0, w, lbl_h) #x, y, width, height
				painter.fillRect(rect, box_color)
				painter.restore()

			if option.state & QStyle.State_MouseOver or\
			    option.state & QStyle.State_Selected:
				title_layout = self.text_layout(title, w, self.title_font, self.title_font_m)
				artist_layout = self.text_layout(artist, w, self.artist_font, self.artist_font_m)
				t_h = title_layout.boundingRect().height()
				a_h = artist_layout.boundingRect().height()

				if gui_constants.GALLERY_FONT_ELIDE:
					draw_text_label(min(t_h+a_h+3, gui_constants.GRIDBOX_LBL_H))
				else:
					draw_text_label(gui_constants.GRIDBOX_LBL_H)

				clipping = QRectF(x, y+gui_constants.THUMB_H_SIZE, w, gui_constants.GRIDBOX_LBL_H - 10)
				title_layout.draw(painter, QPointF(x, y+gui_constants.THUMB_H_SIZE),
					  clip=clipping)
				artist_layout.draw(painter, QPointF(x, y+gui_constants.THUMB_H_SIZE+t_h),
					   clip=clipping)
				#painter.fillRect(option.rect, QColor)
			else:
				if gui_constants.GALLERY_FONT_ELIDE:
					draw_text_label(self.text_label_h)
				else:
					draw_text_label(gui_constants.GRIDBOX_LBL_H)
				# draw text
				painter.save()
				alignment = QTextOption(Qt.AlignCenter)
				alignment.setUseDesignMetrics(True)
				title_rect = QRectF(0,0,w, self.title_font_m.height())
				artist_rect = QRectF(0,self.artist_font_m.height(),w,
						 self.artist_font_m.height())
				painter.translate(x, y+gui_constants.THUMB_H_SIZE)
				if gui_constants.GALLERY_FONT_ELIDE:
					painter.setFont(self.title_font)
					painter.setPen(QColor(title_color))
					painter.drawText(title_rect,
							 self.title_font_m.elidedText(title, Qt.ElideRight, w-10),
							 alignment)
				
					painter.setPen(QColor(artist_color))
					painter.setFont(self.artist_font)
					alignment.setWrapMode(QTextOption.NoWrap)
					painter.drawText(artist_rect,
								self.title_font_m.elidedText(artist, Qt.ElideRight, w-10),
								alignment)
				else:
					text_area.setDefaultFont(QFont(self.font_name))
					text_area.drawContents(painter)
				##painter.resetTransform()
				painter.restore()
				self.popup_window.hide()

			if option.state & QStyle.State_Selected:
				painter.fillRect(option.rect, QColor(164,164,164,120))

			#if option.state & QStyle.State_Selected:
			#	painter.setPen(QPen(option.palette.highlightedText().color()))
		else:
			super().paint(painter, option, index)

	def text_layout(self, text, width, font, font_metrics):
		"Lays out wrapped text"
		text_option = QTextOption(Qt.AlignCenter)
		text_option.setUseDesignMetrics(True)
		text_option.setWrapMode(QTextOption.WordWrap)
		layout = QTextLayout(text, font)
		layout.setTextOption(text_option)
		leading = font_metrics.leading()
		height = 0
		layout.setCacheEnabled(True)
		layout.beginLayout()
		while True:
			line = layout.createLine()
			if not line.isValid():
				break
			line.setLineWidth(width)
			height += leading
			line.setPosition(QPointF(0, height))
			height += line.height()
		layout.endLayout()
		return layout

	def sizeHint(self, StyleOptionViewItem, QModelIndex):
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
		self.parent_widget = parent
		self.setViewMode(self.IconMode)
		self.H = gui_constants.GRIDBOX_H_SIZE
		self.W = gui_constants.GRIDBOX_W_SIZE
		self.setGridSize(QSize(self.W, self.H))
		self.setResizeMode(self.Adjust)
		self.setIconSize(QSize(gui_constants.THUMB_W_SIZE,
						 gui_constants.THUMB_H_SIZE))
		# all items have the same size (perfomance)
		self.setUniformItemSizes(True)
		self.setSelectionBehavior(self.SelectItems)
		self.setSelectionMode(self.ExtendedSelection)
		# improve scrolling
		self.setVerticalScrollMode(self.ScrollPerPixel)
		self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.setLayoutMode(self.SinglePass)
		self.setBatchSize(1)#gui_constants.PREFETCH_ITEM_AMOUNT)
		self.setMouseTracking(True)
		self.sort_model = SortFilterModel()
		self.sort_model.setDynamicSortFilter(True)
		self.sort_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
		self.sort_model.setSortLocaleAware(True)
		self.sort_model.setSortCaseSensitivity(Qt.CaseInsensitive)
		self.manga_delegate = CustomDelegate(parent)
		self.setItemDelegate(self.manga_delegate)
		self.gallery_model = GalleryModel(parent)
		self.sort_model.change_model(self.gallery_model)
		self.sort_model.sort(0)
		self.sort_model.ROWCOUNT_CHANGE.connect(self.gallery_model.ROWCOUNT_CHANGE.emit)
		self.setModel(self.sort_model)
		self.SERIES_DIALOG.connect(self.spawn_dialog)
		self.doubleClicked.connect(self.open_chapter)

		self.current_sort = gui_constants.CURRENT_SORT
		self.sort(self.current_sort)

		if gui_constants.DEBUG:
			def debug_print(a):
				print(a.data(Qt.UserRole+1))
			self.clicked.connect(debug_print)
	#	self.ti = QTimer()
	#	self.ti.timeout.connect(self.test_)
	#	self.ti.start(5000)

	#def test_(self):
	#	"find all galleries in viewport"
	#	def col_next_prepare(index):
	#		"Calculates where the next index is"
	#		rect = self.visualRect(index)
	#		new_col = QPoint(rect.x() + rect.width() + rect.width(),
	#					   rect.y())
	#		return new_col

	#	#find first index locatiion. A wild guess!!
	#	f_indx = self.indexAt(QPoint(87,130))
	#	found = 1
	#	f_rect = self.visualRect(f_indx) # need the first index's rect
	#	row = 1 # which row are we on
	#	while row: # while row is is valid
	#		rect = self.visualRect(f_indx) # rect of current index
	#		next_col_point = col_next_prepare(f_indx)
	#		#calculate the next row
	#		next_row_point = QPoint(f_rect.x()+10,
	#					   rect.y()+rect.height()+(rect.height()//2))
	#		found += 1
	#		# while there are stil more colums
	#		while self.viewport().rect().contains(next_col_point,
	#								  proper=True):
	#			next_indx = self.indexAt(next_col_point) # find the next index
	#			if not next_indx:
	#				break
	#			found += 1
	#			# time to prepare the next iteration
	#			next_col_point = col_next_prepare(next_indx)
	#			print('Moving to next col')
			
	#		if self.viewport().rect().contains(next_row_point, proper=True):
	#			f_indx = self.indexAt(next_row_point)
	#			if f_indx.isValid():
	#				row += 1
	#				print('Moving to next row')
	#		row = None

	#	print('Found ', found)

	def remove_gallery(self, index_list, local=False):
		msgbox = QMessageBox()
		msgbox.setIcon(msgbox.Question)
		msgbox.setStandardButtons(msgbox.Yes | msgbox.No)
		if len(index_list) > 1:
			if not local:
				msg = 'Are you sure you want to remove {} selected galleries?'.format(
				len(index_list))
			else:
				msg = 'Are you sure you want to remove {} selected galleries and their files/directories?'.format(
				len(index_list))

			msgbox.setText(msg)
		else:
			if not local:
				msg = 'Are you sure you want to remove this gallery?'
			else:
				msg = 'Are you sure you want to remove this gallery and its file/directory?'
			msgbox.setText(msg)

		if msgbox.exec() == msgbox.Yes:
			gallery_list = []
			log_i('Removing {} galleries'.format(len(gallery_list)))
			for index in index_list:
				gallery = index.data(Qt.UserRole+1)
				if index.isValid() and gallery:
					#self.rowsAboutToBeRemoved(index.parent(), index.row(), index.row())
					self.gallery_model.removeRows(index.row(), 1)
					gallery_list.append(gallery)
					log_i('Attempt to remove: {} by {}'.format(gallery.title.encode(),
												gallery.artist.encode()))
			gallerydb.add_method_queue(gallerydb.GalleryDB.del_gallery, True, gallery_list, local)
			self.STATUS_BAR_MSG.emit('Gallery removed!')

	def favorite(self, index):
		assert isinstance(index, QModelIndex)
		gallery = index.data(Qt.UserRole+1)
		if gallery.fav == 1:
			gallery.fav = 0
			#self.model().replaceRows([gallery], index.row(), 1, index)
			gallerydb.add_method_queue(gallerydb.GalleryDB.fav_gallery_set, True, gallery.id, 0)
			self.gallery_model.CUSTOM_STATUS_MSG.emit("Unfavorited")
		else:
			gallery.fav = 1
			#self.model().replaceRows([gallery], index.row(), 1, index)
			gallerydb.add_method_queue(gallerydb.GalleryDB.fav_gallery_set, True, gallery.id, 1)
			self.gallery_model.CUSTOM_STATUS_MSG.emit("Favorited")

	def open_random_gallery(self):
		g = random.randint(0, self.gallery_model._data_count-1)
		indx = self.gallery_model.index(g, 1)
		chap_numb = 0
		if gui_constants.RANDOM_GALLERY_CHAPTERS:
			gallery = indx.data(Qt.UserRole)
			b = len(gallery.chapters)
			if b > 1:
				chap_numb = random.randint(0, b-1)

		self.open_chapter(indx, chap_numb)

	def duplicate_check(self, simple=True):
		mode = 'simple' if simple else 'advanced'
		log_i('Checking for duplicates in mode: {}'.format(mode))
		notifbar = self.parent_widget.notification_bar
		notifbar.add_text('Checking for duplicates...')
		if simple:
			galleries = self.gallery_model._data
			duplicates = []
			for g in galleries:
				notifbar.add_text('Checking gallery {}'.format(g.id))
				for y in galleries:
					title = g.title.strip().lower() == y.title.strip().lower()
					path = os.path.normcase(g.path) == os.path.normcase(y.path)
					if g.id != y.id and (title or path):
						if g not in duplicates:
							duplicates.append(y)
							duplicates.append(g)
			if duplicates:
				notifbar.add_text('Found {} duplicates!'.format(len(duplicates)))
				log_d('Found {} duplicates'.format(len(duplicates)))
				g_widget = file_misc.GalleryPopup(("These galleries are found to"+
										  " be duplicates.", duplicates), self.parentWidget())
				buttons = g_widget.add_buttons("Close")
				buttons[0].clicked.connect(g_widget.close)
			else:
				notifbar.add_text('No duplicates found!')

	def open_chapter(self, index, chap_numb=0):
		if not isinstance(index, list):
			index = [index]
		for x in index:
			gallery = x.data(Qt.UserRole+1)
			if len(index) > 1:
				self.STATUS_BAR_MSG.emit("Opening chapters of selected galleries")
			else:
				self.STATUS_BAR_MSG.emit("Opening chapter {} of {}".format(chap_numb+1, gallery.title))
			try:
				if gallery.is_archive:
					gallerydb.add_method_queue(utils.open_chapter, True, gallery.chapters[chap_numb], gallery.path)
				else:
					gallerydb.add_method_queue(utils.open_chapter, True, gallery.chapters[chap_numb])
				if not gallery.times_read:
					gallery.times_read = 0
				gallery.times_read += 1
				gallerydb.add_method_queue(gallerydb.GalleryDB.modify_gallery, True, gallery.id, times_read=gallery.times_read)
			except IndexError:
				pass

	def del_chapter(self, index, chap_numb):
		gallery = index.data(Qt.UserRole+1)
		if len(gallery.chapters) < 2:
			self.remove_gallery([index])
		else:
			msgbox = QMessageBox(self)
			msgbox.setText('Are you sure you want to delete:')
			msgbox.setIcon(msgbox.Question)
			msgbox.setInformativeText('Chapter {} of {}'.format(chap_numb+1,
														  gallery.title))
			msgbox.setStandardButtons(msgbox.Yes | msgbox.No)
			if msgbox.exec() == msgbox.Yes:
				gallery.chapters.pop(chap_numb, None)
				self.gallery_model.replaceRows([gallery], index.row())
				gallerydb.add_method_queue(gallerydb.ChapterDB.del_chapter, True, gallery.id, chap_numb)

	def refresh(self):
		#self.gallery_model.layoutChanged.emit() # TODO: CAUSE OF CRASH! FIX ASAP
		#self.STATUS_BAR_MSG.emit("Refreshed")
		pass

	def sort(self, name):
		if name == 'title':
			self.sort_model.setSortRole(Qt.DisplayRole)
			self.sort_model.sort(0, Qt.AscendingOrder)
			self.current_sort = 'title'
		elif name == 'artist':
			self.sort_model.setSortRole(Qt.UserRole+2)
			self.sort_model.sort(0, Qt.AscendingOrder)
			self.current_sort = 'artist'
		elif name == 'date_added':
			self.sort_model.setSortRole(Qt.UserRole+4)
			self.sort_model.sort(0, Qt.DescendingOrder)
			self.current_sort = 'date_added'
		elif name == 'pub_date':
			self.sort_model.setSortRole(Qt.UserRole+5)
			self.sort_model.sort(0, Qt.DescendingOrder)
			self.current_sort = 'pub_date'

	def contextMenuEvent(self, event):
		handled = False
		custom = False
		index = self.indexAt(event.pos())
		index = self.sort_model.mapToSource(index)

		selected = False
		select_indexes = self.selectedIndexes()
		if len(select_indexes) > 1:
			selected = True

		def asc_desc():
			if self.sort_model.sortOrder() == Qt.AscendingOrder:
				self.sort_model.sort(0, Qt.DescendingOrder)
			else:
				self.sort_model.sort(0, Qt.AscendingOrder)

		if index.isValid():
			self.manga_delegate.CONTEXT_ON = True
			if selected:
				menu = misc.GalleryMenu(self, index, self.gallery_model,
							   self.parent_widget, select_indexes)
			else:
				menu = misc.GalleryMenu(self, index, self.gallery_model,
							   self.parent_widget)
			handled = True
		else:
			menu = QMenu(self)
			add_gallery = QAction("&Add new Gallery...", menu,
						triggered = self.SERIES_DIALOG.emit)
			menu.addAction(add_gallery)
			def set_current_sort(act, key):
				if self.current_sort == key:
					act.setChecked(True)
			sort_main = QAction("&Sort by", menu)
			menu.addAction(sort_main)
			sort_menu = QMenu()
			sort_main.setMenu(sort_menu)
			sort_actions = QActionGroup(sort_menu, exclusive=True)
			asc_desc_act = QAction("Asc/Desc", sort_menu)
			asc_desc_act.triggered.connect(asc_desc)
			s_title = sort_actions.addAction(QAction("Title", sort_actions, checkable=True))
			s_title.triggered.connect(functools.partial(self.sort, 'title'))
			set_current_sort(s_title, 'title')
			s_artist = sort_actions.addAction(QAction("Author", sort_actions, checkable=True))
			s_artist.triggered.connect(functools.partial(self.sort, 'artist'))
			set_current_sort(s_artist, 'artist')
			s_date = sort_actions.addAction(QAction("Date Added", sort_actions, checkable=True))
			s_date.triggered.connect(functools.partial(self.sort, 'date_added'))
			set_current_sort(s_date, 'date_added')
			s_pub_d = sort_actions.addAction(QAction("Date Published", sort_actions, checkable=True))
			s_pub_d.triggered.connect(functools.partial(self.sort, 'pub_date'))
			set_current_sort(s_pub_d, 'pub_date')

			sort_menu.addAction(asc_desc_act)
			sort_menu.addSeparator()
			sort_menu.addAction(s_title)
			sort_menu.addAction(s_artist)
			sort_menu.addAction(s_date)
			sort_menu.addAction(s_pub_d)

			handled = True

		if handled:
			menu.exec_(event.globalPos())
			self.manga_delegate.CONTEXT_ON = False
			event.accept()
			del menu
		else:
			event.ignore()

	#need this for debugging purposes
	def resizeEvent(self, resizeevent):
		super().resizeEvent(resizeevent)
		#print(resizeevent.size())

	def find_index(self, gallery_id):
		"Finds and returns the index associated with the gallery id"
		index = None
		rows = self.gallery_model.rowCount()
		for r in range(rows):
			indx = self.gallery_model.index(r, 1)
			m_gallery = indx.data(Qt.UserRole+1)
			if m_gallery.id == gallery_id:
				index = indx
				break
		return index

	def replace_edit_gallery(self, list_of_gallery, pos=None):
		"Replaces the view and DB with given list of gallery, at given position"
		assert isinstance(list_of_gallery, (list, gallerydb.Gallery)), "Please pass a gallery to replace with"
		if isinstance(list_of_gallery, gallerydb.Gallery):
			list_of_gallery = [list_of_gallery]
		log_d('Replacing {} galleries'.format(len(list_of_gallery)))
		for gallery in list_of_gallery:
			if not pos:
				index = self.find_index(gallery.id)
				if not index:
					log_e('Could not find index for gallery to edit: {}'.format(
						gallery.title.encode(errors='ignore')))
					continue
				pos = index.row()
			kwdict = {'title':gallery.title,
			 'profile':gallery.profile,
			 'artist':gallery.artist,
			 'info':gallery.info,
			 'type':gallery.type,
			 'language':gallery.language,
			 'status':gallery.status,
			 'pub_date':gallery.pub_date,
			 'tags':gallery.tags,
			 'link':gallery.link,
			 'series_path':gallery.path,
			 'chapters':gallery,
			 'exed':gallery.exed}

			gallerydb.add_method_queue(gallerydb.GalleryDB.modify_gallery,
							 True, gallery.id, **kwdict)
		assert isinstance(pos, int)
		self.gallery_model.replaceRows([gallery], pos, len(list_of_gallery))

	def spawn_dialog(self, index=False):
		if not index:
			dialog = gallerydialog.GalleryDialog(self.parent_widget)
			dialog.SERIES.connect(self.gallery_model.addRows)
		else:
			dialog = gallerydialog.GalleryDialog(self.parent_widget, [index])
			dialog.SERIES_EDIT.connect(self.replace_edit_gallery)
		
		dialog.show()

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
		self.parent_widget = parent
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
		self.doubleClicked.connect(self.parent_widget.manga_list_view.open_chapter)

	# display tooltip only for elided text
	#def viewportEvent(self, event):
	#	if event.type() == QEvent.ToolTip:
	#		h_event = QHelpEvent(event)
	#		index = self.indexAt(h_event.pos())
	#		if index.isValid():
	#			size_hint = self.itemDelegate(index).sizeHint(self.viewOptions(),
	#											  index)
	#			rect = QRect(0, 0, size_hint.width(), size_hint.height())
	#			rect_visual = self.visualRect(index)
	#			if rect.width() <= rect_visual.width():
	#				QToolTip.hideText()
	#				return True
	#	return super().viewportEvent(event)

	def refresh(self):
		#self.gallery_model.layoutChanged.emit()
		##self.gallery_model.populate_data() # TODO: CAUSE OF CRASH! FIX ASAP
		#self.STATUS_BAR_MSG.emit("Refreshed")
		pass

	def contextMenuEvent(self, event):
		handled = False
		index = self.indexAt(event.pos())
		index = self.sort_model.mapToSource(index)

		selected = False
		select_indexes = self.selectedIndexes()
		if len(select_indexes) > len(gui_constants.COLUMNS):
			selected = True

		if index.isValid():
			if selected:
				menu = misc.GalleryMenu(self, 
							index,
							self.parent_widget.manga_list_view.gallery_model,
							self.parent_widget, select_indexes)
			else:
				menu = misc.GalleryMenu(self, index, self.gallery_model,
							   self.parent_widget)
			handled = True

		if handled:
			menu.exec_(event.globalPos())
			event.accept()
			del menu
		else:
			event.ignore()

if __name__ == '__main__':
	raise NotImplementedError("Unit testing not yet implemented")
