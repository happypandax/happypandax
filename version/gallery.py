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

import threading, logging, os, math, functools, random, datetime
import re as regex

from PyQt5.QtCore import (Qt, QAbstractListModel, QModelIndex, QVariant,
						  QSize, QRect, QEvent, pyqtSignal, QThread,
						  QTimer, QPointF, QSortFilterProxyModel,
						  QAbstractTableModel, QItemSelectionModel,
						  QPoint, QRectF, QDate, QDateTime, QObject,
						  QEvent, QSizeF)
from PyQt5.QtGui import (QPixmap, QBrush, QColor, QPainter, 
						 QPen, QTextDocument,
						 QMouseEvent, QHelpEvent,
						 QPixmapCache, QCursor, QPalette, QKeyEvent,
						 QFont, QTextOption, QFontMetrics, QFontMetricsF,
						 QTextLayout, QPainterPath, QScrollPrepareEvent,
						 QWheelEvent)
from PyQt5.QtWidgets import (QListView, QFrame, QLabel,
							 QStyledItemDelegate, QStyle,
							 QMenu, QAction, QToolTip, QVBoxLayout,
							 QSizePolicy, QTableWidget, QScrollArea,
							 QHBoxLayout, QFormLayout, QDesktopWidget,
							 QWidget, QHeaderView, QTableView, QApplication,
							 QMessageBox, QActionGroup, QScroller)

import gallerydb
import app_constants
import misc
import gallerydialog
import io_misc
import utils

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical

class GallerySearch(QObject):
	FINISHED = pyqtSignal()
	def __init__(self, data):
		super().__init__()
		self._data = data
		self.result = {}

		# filtering
		self.fav = False

	def set_data(self, new_data):
		self._data = new_data
		self.result = {g.id: True for g in self._data}

	def set_fav(self, new_fav):
		self.fav = new_fav

	def search(self, term):
		term = ' '.join(term.split())
		search_pieces = utils.get_terms(term)

		self._filter(search_pieces)
		self.FINISHED.emit()

	def _filter(self, terms):
		self.result.clear()
		for gallery in self._data:
			if self.fav:
				if not gallery.fav:
					continue
			all_terms = {t: False for t in terms}
			allow = False
			if utils.all_opposite(terms):
				self.result[gallery.id] = True
				continue
			
			for t in terms:
				if t in gallery:
					all_terms[t] = True

			if all(all_terms.values()):
				allow = True

			self.result[gallery.id] = allow

class SortFilterModel(QSortFilterProxyModel):
	ROWCOUNT_CHANGE = pyqtSignal()
	_DO_SEARCH = pyqtSignal(str)
	_CHANGE_SEARCH_DATA = pyqtSignal(list)
	_CHANGE_FAV = pyqtSignal(bool)

	HISTORY_SEARCH_TERM = pyqtSignal(str)
	# Navigate terms
	NEXT, PREV = range(2)
	# Views
	CAT_VIEW, FAV_VIEW = range(2)

	def __init__(self, parent=None):
		super().__init__(parent)
		self._data = app_constants.GALLERY_DATA
		self._search_ready = False
		self.current_term = ''
		self.terms_history = []
		self.current_term_history = 0

		self.current_view = self.CAT_VIEW

	def navigate_history(self, direction=PREV):
		new_term = ''
		if self.terms_history:
			if direction == self.NEXT:
				if self.current_term_history < len(self.terms_history) - 1:
					self.current_term_history += 1
			elif direction == self.PREV:
				if self.current_term_history > 0:
					self.current_term_history -= 1
			new_term = self.terms_history[self.current_term_history]
			if new_term != self.current_term:
				self.init_search(new_term, False)
		return new_term


	def fetchMore(self, index):
		return super().fetchMore(index)

	def fav_view(self):
		self._CHANGE_FAV.emit(True)
		self._DO_SEARCH.emit('')
		self.current_view = self.FAV_VIEW

	def catalog_view(self):
		self._CHANGE_FAV.emit(False)
		self._DO_SEARCH.emit('')
		self.current_view = self.CAT_VIEW

	def setup_search(self):
		if not self._search_ready:
			self.gallery_search = GallerySearch(self._data)
			self.gallery_search.FINISHED.connect(self.invalidateFilter)
			self.gallery_search.FINISHED.connect(lambda: self.ROWCOUNT_CHANGE.emit())
			self.gallery_search.moveToThread(app_constants.GENERAL_THREAD)
			self._DO_SEARCH.connect(self.gallery_search.search)
			self._CHANGE_SEARCH_DATA.connect(self.gallery_search.set_data)
			self._CHANGE_FAV.connect(self.gallery_search.set_fav)
			self._search_ready = True

	def init_search(self, term='', history=True):
		"""
		Receives a search term and initiates a search
		"""
		if term and history:
			if len(self.terms_history) > 10:
				self.terms_history = self.terms_history[-10:]
			self.terms_history.append(term)

			self.current_term_history = len(self.terms_history) - 1
			if self.current_term_history < 0:
				self.current_term_history = 0

		self.current_term = term
		if not history:
			self.HISTORY_SEARCH_TERM.emit(term)
		self._DO_SEARCH.emit(term)

	def filterAcceptsRow(self, source_row, parent_index):
		if self.sourceModel():
			index = self.sourceModel().index(source_row, 0, parent_index)
			if index.isValid():
				if self._search_ready:
					gallery = index.data(Qt.UserRole+1)
					try:
						return self.gallery_search.result[gallery.id]
					except KeyError:
						pass
				else:
					return True
		return False
	
	def change_model(self, model):
		self.setSourceModel(model)
		self._data = self.sourceModel()._data
		self._CHANGE_SEARCH_DATA.emit(self._data)

	def change_data(self, data):
		self._CHANGE_SEARCH_DATA.emit(data)

	def populate_data(self):
		self.sourceModel().populate_data()

	def status_b_msg(self, msg):
		self.sourceModel().status_b_msg(msg)

	def addRows(self, list_of_gallery, position=None,
				rows=1, index = QModelIndex()):
		if not position:
			log_d('Add rows: No position specified')
			position = len(self._data)
		self.beginInsertRows(index, position, position + rows - 1)
		self.sourceModel().addRows(list_of_gallery, position, rows, index)
		self.endInsertRows()
		#self.modelReset.emit()

	def insertRows(self, list_of_gallery, position=None,
				rows=None, index = QModelIndex(), data_count=True):
		position = len(self._data) if not position else position
		rows = len(list_of_gallery) if not rows else 0
		self.beginInsertRows(index, position, position + rows - 1)
		self.sourceModel().insertRows(list_of_gallery, position, rows,
								index, data_count)
		self.endInsertRows()
		#self.modelReset.emit()

	def replaceRows(self, list_of_gallery, position, rows=1, index=QModelIndex()):
		self.sourceModel().replaceRows(list_of_gallery, position, rows, index)

	def removeRows(self, position, rows=1, index=QModelIndex()):
		"Deletes gallery data from the model data list. OBS: doesn't touch DB!"
		self.beginRemoveRows(QModelIndex(), position, position + rows - 1)
		self.sourceModel().removeRows(position, rows, index)
		self.endRemoveRows()
		return True

class GalleryModel(QAbstractTableModel):
	"""
	Model for Model/View/Delegate framework
	"""

	ROWCOUNT_CHANGE = pyqtSignal()
	STATUSBAR_MSG = pyqtSignal(str)
	CUSTOM_STATUS_MSG = pyqtSignal(str)
	ADDED_ROWS = pyqtSignal()
	ADD_MORE = pyqtSignal()
	_data = app_constants.GALLERY_DATA

	REMOVING_ROWS = False

	def __init__(self, parent=None):
		super().__init__(parent)
		self.dataChanged.connect(lambda: self.status_b_msg("Edited"))
		self.dataChanged.connect(lambda: self.ROWCOUNT_CHANGE.emit())
		self.layoutChanged.connect(lambda: self.ROWCOUNT_CHANGE.emit())
		self.CUSTOM_STATUS_MSG.connect(self.status_b_msg)
		self._TITLE = app_constants.TITLE
		self._ARTIST = app_constants.ARTIST
		self._TAGS = app_constants.TAGS
		self._TYPE = app_constants.TYPE
		self._FAV = app_constants.FAV
		self._CHAPTERS = app_constants.CHAPTERS
		self._LANGUAGE = app_constants.LANGUAGE
		self._LINK = app_constants.LINK
		self._DESCR = app_constants.DESCR
		self._DATE_ADDED = app_constants.DATE_ADDED
		self._PUB_DATE = app_constants.PUB_DATE

		self._data_count = 0 # number of items added to model
		self.db_emitter = gallerydb.DatabaseEmitter()
		self.db_emitter.GALLERY_EMITTER.connect(lambda a: self.insertRows(a, emit_statusbar=False))

	def populate_data(self, galleries):
		"Populates the model in a timely manner"
		t = 0
		for pos, gallery in enumerate(galleries):
			t += 100
			if not gallery.valid:
				reasons = gallery.invalidities()
			else:
				QTimer.singleShot(t, functools.partial(self.insertRows, [gallery], pos))

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
					return 'No date set'

		# TODO: name all these roles and put them in app_constants...

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
			return bg_color

		if app_constants.GRID_TOOLTIP and role == Qt.ToolTipRole:
			add_bold = []
			add_tips = []
			if app_constants.TOOLTIP_TITLE:
				add_bold.append('<b>Title:</b>')
				add_tips.append(current_gallery.title)
			if app_constants.TOOLTIP_AUTHOR:
				add_bold.append('<b>Author:</b>')
				add_tips.append(current_gallery.artist)
			if app_constants.TOOLTIP_CHAPTERS:
				add_bold.append('<b>Chapters:</b>')
				add_tips.append(len(current_gallery.chapters))
			if app_constants.TOOLTIP_STATUS:
				add_bold.append('<b>Status:</b>')
				add_tips.append(current_gallery.status)
			if app_constants.TOOLTIP_TYPE:
				add_bold.append('<b>Type:</b>')
				add_tips.append(current_gallery.type)
			if app_constants.TOOLTIP_LANG:
				add_bold.append('<b>Language:</b>')
				add_tips.append(current_gallery.language)
			if app_constants.TOOLTIP_DESCR:
				add_bold.append('<b>Description:</b><br />')
				add_tips.append(current_gallery.info)
			if app_constants.TOOLTIP_TAGS:
				add_bold.append('<b>Tags:</b>')
				add_tips.append(utils.tag_to_string(
					current_gallery.tags))
			if app_constants.TOOLTIP_LAST_READ:
				add_bold.append('<b>Last read:</b>')
				add_tips.append(
					'{} ago'.format(utils.get_date_age(current_gallery.last_read)) if current_gallery.last_read else "Never!")
			if app_constants.TOOLTIP_TIMES_READ:
				add_bold.append('<b>Times read:</b>')
				add_tips.append(current_gallery.times_read)
			if app_constants.TOOLTIP_PUB_DATE:
				add_bold.append('<b>Publication Date:</b>')
				add_tips.append('{}'.format(current_gallery.pub_date).split(' ')[0])
			if app_constants.TOOLTIP_DATE_ADDED:
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

		if role == Qt.UserRole+6:
			return current_gallery.times_read



		return None

	def rowCount(self, index = QModelIndex()):
		if not index.isValid():
			return self._data_count
		else:
			return 0

	def columnCount(self, parent = QModelIndex()):
		return len(app_constants.COLUMNS)

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
		if self.REMOVING_ROWS:
			return False
		self.ADD_MORE.emit()
		log_d('Adding {} rows'.format(rows))
		if not position:
			log_d('Add rows: No position specified')
			position = len(self._data)
		self._data_count += len(list_of_gallery)
		self.beginInsertRows(QModelIndex(), position, position + rows - 1)
		log_d('Add rows: Began inserting')
		gallerydb.GalleryDB.begin()
		for gallery in list_of_gallery:
			gallerydb.add_method_queue(gallerydb.GalleryDB.add_gallery_return, True, gallery)
			gallery.profile = gallerydb.PROFILE_TO_MODEL.get()
			self._data.insert(position, gallery)
		gallerydb.add_method_queue(gallerydb.GalleryDB.end, True)
		log_d('Add rows: Finished inserting')
		self.endInsertRows()
		gallerydb.add_method_queue(self.db_emitter.update_count, True)
		self.CUSTOM_STATUS_MSG.emit("Added item(s)")
		self.ROWCOUNT_CHANGE.emit()
		self.ADDED_ROWS.emit()
		return True

	def insertRows(self, list_of_gallery, position=None,
				rows=None, index = QModelIndex(), emit_statusbar=True, data_count=True):
		"Inserts new gallery data to the data list WITHOUT adding to DB"
		if self.REMOVING_ROWS:
			return False
		self.ADD_MORE.emit()
		position = len(self._data) if not position else position
		rows = len(list_of_gallery) if not rows else 0
		if data_count:
			self._data_count += len(list_of_gallery)
		self.beginInsertRows(QModelIndex(), position, position + rows - 1)
		self._data.extend(list_of_gallery)
		self.endInsertRows()
		gallerydb.add_method_queue(self.db_emitter.update_count, True)
		if emit_statusbar:
			self.CUSTOM_STATUS_MSG.emit("Added item(s)")
		self.ROWCOUNT_CHANGE.emit()
		self.ADDED_ROWS.emit()
		return True

	def replaceRows(self, list_of_gallery, position, rows=1, index=QModelIndex()):
		"replaces gallery data to the data list WITHOUT adding to DB"
		for pos, gallery in enumerate(list_of_gallery):
			del self._data[position+pos]
			self._data.insert(position+pos, gallery)
		self.dataChanged.emit(index, index, [Qt.UserRole+1, Qt.DecorationRole])

	def removeRows(self, position, rows=1, index=QModelIndex()):
		"Deletes gallery data from the model data list. OBS: doesn't touch DB!"
		self._data_count -= rows
		self.beginRemoveRows(QModelIndex(), position, position + rows - 1)
		for r in range(rows):
			del self._data[position]
		self.endRemoveRows()
		gallerydb.add_method_queue(self.db_emitter.update_count, False)
		self.ROWCOUNT_CHANGE.emit()
		return True

	def canFetchMore(self, index):
		return self.db_emitter.can_fetch_more()

	def fetchMore(self, index):
		self.db_emitter.fetch_more()

class CustomDelegate(QStyledItemDelegate):
	def __init__(self, parent=None):
		super().__init__(parent)

	def text_layout(self, text, width, font, font_metrics, alignment=Qt.AlignCenter):
		"Lays out wrapped text"
		text_option = QTextOption(alignment)
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

class ListDelegate(CustomDelegate):
	"A custom delegate for the model/view framework"

	def __init__(self, parent):
		super().__init__(parent)
		self.dynamic_width = app_constants.LISTBOX_W_SIZE
		self.dynamic_height = app_constants.LISTBOX_H_SIZE
		self.parent_font_m = parent.fontMetrics()
		self.parent_font = parent.font()
		self.title_font = QFont()
		self.title_font.setPointSize(10)
		self.title_font.setBold(True)
		self.artist_font = QFont()
		self.artist_font.setPointSize(9)
		self.artist_font_m = QFontMetrics(self.artist_font)
		self.title_font_m = QFontMetrics(self.title_font)

		self.pic_width = 122
		self.pic_height = 172
		self._pic_margin = 10

	def paint(self, painter, option, index):
		assert isinstance(painter, QPainter)
		if index.data(Qt.UserRole+1):
			c_gallery = index.data(Qt.UserRole+1)

			start_x = x = option.rect.x()
			y = option.rect.y()
			w = option.rect.width()
			h = option.rect.height()

			if app_constants.HIGH_QUALITY_THUMBS:
				painter.setRenderHint(QPainter.SmoothPixmapTransform)
			painter.setRenderHint(QPainter.Antialiasing)

			# border
			painter.setPen(QColor("#A6A6B7"))
			painter.drawRect(option.rect)

			# background
			painter.setBrush(QBrush(QColor("#464646")))
			painter.drawRect(option.rect)

			# pic
			pic_rect = QRect(x+self._pic_margin, y+self._pic_margin, self.pic_width, self.pic_height)
			painter.setBrush(QBrush(QColor("white")))
			painter.drawRect(pic_rect)

			# remaining rect with left margin
			star_x = x + w - self._pic_margin
			x = pic_rect.x() + pic_rect.width() + self._pic_margin*2
			w -= (pic_rect.width() + self._pic_margin)

			# title & artist
			title_margin = 40
			title_top_margin = 15
			title_x = x + title_margin
			title_y = y + title_top_margin
			title_width = w - title_margin
			title_layout = self.text_layout(c_gallery.title, title_width-title_margin, self.title_font, self.title_font_m)
			painter.setPen(QColor("white"))
			title_layout.draw(painter, QPointF(title_x, title_y))

			artist_layout = self.text_layout(c_gallery.artist, title_width-title_margin, self.artist_font, self.artist_font_m)
			painter.setPen(QColor("#A6A6B7"))
			title_rect = title_layout.boundingRect()
			artist_y = title_y+title_rect.height()
			artist_layout.draw(painter, QPointF(title_x, artist_y))

			# meta info
			start_y = y + title_rect.height()+title_top_margin+artist_layout.boundingRect().height()
			txt_height = painter.fontMetrics().height()
			txt_list = self.gallery_info(c_gallery)
			for g_data in txt_list:
				painter.drawText(x, start_y, g_data)
				start_y += txt_height + 3
			# descr
			descr_y = artist_y + artist_layout.boundingRect().height()
			descr_x = title_x + (painter.fontMetrics().width(txt_list[6])*1.1)
			descr_layout = self.text_layout(c_gallery.info, title_width, painter.font(), painter.fontMetrics(), Qt.AlignLeft)
			descr_layout.draw(painter, QPointF(descr_x, descr_y))

			# tags
			tags_y = descr_y + descr_layout.boundingRect().height()
			tags_h = painter.fontMetrics().height() * 1.1
			tags_y += tags_h

			for ns in c_gallery.tags:
				ns_text = "{}:".format(ns)
				painter.drawText(descr_x, tags_y, ns_text)
				tag_x = descr_x + painter.fontMetrics().width(ns_text) * 1.2
				tags_txt = self.tags_text(c_gallery.tags[ns])
				tags_layout = self.text_layout(tags_txt, w-(tag_x*1.1 - x), painter.font(), painter.fontMetrics(), Qt.AlignLeft)
				tags_layout.draw(painter, QPointF(tag_x, tags_y-tags_h*0.7))
				tags_y += tags_layout.boundingRect().height()

			# fav star
			if c_gallery.fav:
				star_pix = QPixmap(app_constants.STAR_PATH)
				star_x -= star_pix.width()
				painter.drawPixmap(star_x, y+5, star_pix)

		else:
			return super().paint(painter, option, index)

	def tags_text(self, tag_list):
		tag_txt = ""
		l = len(tag_list)
		for n, tag in enumerate(tag_list, 1):
			if n == l:
				tag_txt += tag
			else:
				tag_txt += "{}, ".format(tag)
		return tag_txt

	def gallery_info(self, c_gallery):
		txt_list = ["Type: {}".format(c_gallery.type), "Chapters: {}".format(c_gallery.chapters.count()),
			   "Language: {}".format(c_gallery.language), "Pages: {}".format(c_gallery.chapters.pages()),
			   "Status: {}".format(c_gallery.status), "Added: {}".format(c_gallery.date_added.strftime('%d %b %Y')),
			   "Published: {}".format(c_gallery.pub_date.strftime('%d %b %Y') if c_gallery.pub_date else "Unknown"),
			   "Last read: {}".format('{} ago'.format(utils.get_date_age(c_gallery.last_read)) if c_gallery.last_read else "Never!")]
		return txt_list

	def sizeHint(self, option, index):
		g = index.data(Qt.UserRole+1)
		margin = 10
		w = option.rect.width()-(self.pic_width+self._pic_margin*2+
						   self.parent_font_m.width("Added: {}".format(g.date_added.strftime('%d %b %Y'))))
		w = abs(w)
		h = self.text_layout(g.info, w, self.parent_font, self.parent_font_m, Qt.AlignLeft).boundingRect().height()
		for ns in g.tags:
			tags = g.tags[ns]
			txt = self.tags_text(tags)
			txt_layout = self.text_layout(txt, w, self.parent_font, self.parent_font_m, Qt.AlignLeft)
			h += txt_layout.boundingRect().height()

		h2 = 0
		title_layout = self.text_layout(g.title, w, self.title_font, self.title_font_m)
		h2 += title_layout.boundingRect().height() + self.title_font_m.height()
		artist_layout = self.text_layout(g.artist, w, self.artist_font, self.artist_font_m)
		h2 += artist_layout.boundingRect().height() + self.artist_font_m.height()
		h2 += self.parent_font_m.height()*len(self.gallery_info(g))
		print("h:", h, "h2", h2)
		if h > app_constants.LISTBOX_H_SIZE:
			dynamic_height = h - self.title_font_m.height()
		else:
			dynamic_height = app_constants.LISTBOX_H_SIZE

		if h2 > app_constants.LISTBOX_H_SIZE > h:
			dynamic_height = h2 + self.title_font_m.height()

		return QSize(self.dynamic_width, dynamic_height)

class GridDelegate(CustomDelegate):
	"A custom delegate for the model/view framework"

	POPUP = pyqtSignal()
	CONTEXT_ON = False

	# Gallery states
	G_NORMAL, G_DOWNLOAD = range(2)

	def __init__(self, parent=None):
		super().__init__(parent)
		QPixmapCache.setCacheLimit(app_constants.THUMBNAIL_CACHE_SIZE[0]*
							 app_constants.THUMBNAIL_CACHE_SIZE[1])
		self._painted_indexes = {}

		#misc.FileIcon.refresh_default_icon()
		self.file_icons = misc.FileIcon()
		if app_constants.USE_EXTERNAL_VIEWER:
			self.external_icon = self.file_icons.get_external_file_icon()
		else:
			self.external_icon = self.file_icons.get_default_file_icon()

		self.font_size = app_constants.GALLERY_FONT[1]
		self.font_name = app_constants.GALLERY_FONT[0]
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
		self.W = app_constants.THUMB_W_SIZE
		self.H = app_constants.THUMB_H_SIZE + app_constants.GRIDBOX_LBL_H#self.text_label_h #+ app_constants.GRIDBOX_LBL_H

	def key(self, key):
		"Assigns an unique key to indexes"
		if key in self._painted_indexes:
			return self._painted_indexes[key]
		else:
			k = hash(key)
			self._painted_indexes[key] = str(k)
			return str(k)

	def paint(self, painter, option, index):
		assert isinstance(painter, QPainter)
		if index.data(Qt.UserRole+1):
			if app_constants.HIGH_QUALITY_THUMBS:
				painter.setRenderHint(QPainter.SmoothPixmapTransform)
			painter.setRenderHint(QPainter.Antialiasing)
			gallery = index.data(Qt.UserRole+1)
			title = gallery.title
			artist = gallery.artist
			title_color = app_constants.GRID_VIEW_TITLE_COLOR
			artist_color = app_constants.GRID_VIEW_ARTIST_COLOR
			label_color = app_constants.GRID_VIEW_LABEL_COLOR
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
				width:{6}px;
				height:{7}px
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
			""".format(title_size, artist_size, title, artist, title_color, artist_color,
			  130+app_constants.SIZE_FACTOR, 1+app_constants.SIZE_FACTOR))
			text_area.setTextWidth(w)

			#chapter_area = QTextDocument()
			#chapter_area.setDefaultFont(option.font)
			#chapter_area.setHtml("""
			#<font color="black">{}</font>
			#""".format("chapter"))
			#chapter_area.setTextWidth(w)
			def center_img(width):
				new_x = x
				if width < w:
					diff = w - width
					offset = diff//2
					new_x += offset
				return new_x

			def img_too_big(start_x):
				txt_layout = self.text_layout("Image is too big!", w, self.title_font, self.title_font_m)

				clipping = QRectF(x, y+h//4, w, app_constants.GRIDBOX_LBL_H - 10)
				txt_layout.draw(painter, QPointF(x, y+h//4),
					  clip=clipping)

			# if we can't find a cached image
			pix_cache = QPixmapCache.find(self.key(gallery.profile))
			if isinstance(pix_cache, QPixmap):
				self.image = pix_cache
				img_x = center_img(self.image.width())
				if self.image.width() > w or self.image.height() > h:
					img_too_big(img_x)
				else:
					if self.image.height() < self.image.width(): #to keep aspect ratio
						painter.drawPixmap(QPoint(img_x,y),
								self.image)
					else:
						painter.drawPixmap(QPoint(img_x,y),
								self.image)
			else:
				self.image = QPixmap(gallery.profile)
				img_x = center_img(self.image.width())
				QPixmapCache.insert(self.key(gallery.profile), self.image)
				if self.image.width() > w or self.image.height() > h:
					img_too_big(img_x)
				else:
					if self.image.height() < self.image.width(): #to keep aspect ratio
						painter.drawPixmap(QPoint(img_x,y),
								self.image)
					else:
						painter.drawPixmap(QPoint(img_x,y),
								self.image)

			# draw star if it's favorited
			if gallery.fav == 1:
				painter.drawPixmap(QPointF(x,y), QPixmap(app_constants.STAR_PATH))
			
			if app_constants._REFRESH_EXTERNAL_VIEWER:
				if app_constants.USE_EXTERNAL_VIEWER:
					self.external_icon = self.file_icons.get_external_file_icon()
				else:
					self.external_icon = self.file_icons.get_default_file_icon()
			
			if gallery.state == self.G_DOWNLOAD:
				painter.save()
				dl_box = QRect(x, y, w, 20)
				painter.setBrush(QBrush(QColor(0,0,0,123)))
				painter.setPen(QColor('white'))
				painter.drawRect(dl_box)
				painter.drawText(dl_box, Qt.AlignCenter, 'Downloading...')
				painter.restore()
			else:
				if app_constants.DISPLAY_GALLERY_TYPE:
					self.type_icon = self.file_icons.get_file_icon(gallery.path)
					if self.type_icon and not self.type_icon.isNull():
						self.type_icon.paint(painter, QRect(x+2, y+app_constants.THUMB_H_SIZE-16, 16, 16))

				if app_constants.USE_EXTERNAL_PROG_ICO:
					if self.external_icon and not self.external_icon.isNull():
						self.external_icon.paint(painter, QRect(x+w-30, y+app_constants.THUMB_H_SIZE-28, 28, 28))

			def draw_text_label(lbl_h):
				#draw the label for text
				painter.save()
				painter.translate(x, y+app_constants.THUMB_H_SIZE)
				box_color = QBrush(QColor(label_color))#QColor(0,0,0,123))
				painter.setBrush(box_color)
				rect = QRect(0, 0, w, lbl_h) #x, y, width, height
				painter.fillRect(rect, box_color)
				painter.restore()
				return rect

			if option.state & QStyle.State_MouseOver or\
			    option.state & QStyle.State_Selected:
				title_layout = self.text_layout(title, w, self.title_font, self.title_font_m)
				artist_layout = self.text_layout(artist, w, self.artist_font, self.artist_font_m)
				t_h = title_layout.boundingRect().height()
				a_h = artist_layout.boundingRect().height()

				if app_constants.GALLERY_FONT_ELIDE:
					lbl_rect = draw_text_label(min(t_h+a_h+3, app_constants.GRIDBOX_LBL_H))
				else:
					lbl_rect = draw_text_label(app_constants.GRIDBOX_LBL_H)

				clipping = QRectF(x, y+app_constants.THUMB_H_SIZE, w, app_constants.GRIDBOX_LBL_H - 10)
				title_layout.draw(painter, QPointF(x, y+app_constants.THUMB_H_SIZE),
					  clip=clipping)
				artist_layout.draw(painter, QPointF(x, y+app_constants.THUMB_H_SIZE+t_h),
					   clip=clipping)
				#painter.fillRect(option.rect, QColor)
			else:
				if app_constants.GALLERY_FONT_ELIDE:
					lbl_rect = draw_text_label(self.text_label_h)
				else:
					lbl_rect = draw_text_label(app_constants.GRIDBOX_LBL_H)
				# draw text
				painter.save()
				alignment = QTextOption(Qt.AlignCenter)
				alignment.setUseDesignMetrics(True)
				title_rect = QRectF(0,0,w, self.title_font_m.height())
				artist_rect = QRectF(0,self.artist_font_m.height(),w,
						 self.artist_font_m.height())
				painter.translate(x, y+app_constants.THUMB_H_SIZE)
				if app_constants.GALLERY_FONT_ELIDE:
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

			if option.state & QStyle.State_Selected:
				painter.save()
				selected_rect = QRectF(x, y, w, lbl_rect.height()+app_constants.THUMB_H_SIZE)
				painter.setPen(Qt.NoPen)
				painter.setBrush(QBrush(QColor(164,164,164,120)))
				#p_path = QPainterPath()
				#p_path.setFillRule(Qt.WindingFill)
				#p_path.addRoundedRect(selected_rect, 5,5)
				#s_factor = app_constants.SIZE_FACTOR + 10
				#p_path.addRect(x,y, s_factor, s_factor)
				#p_path.addRect(x+w-s_factor,y, s_factor, s_factor)
				#painter.drawPath(p_path.simplified())
				painter.drawRoundedRect(selected_rect, 5, 5)
				#painter.fillRect(selected_rect, QColor(164,164,164,120))
				painter.restore()

			if gallery.dead_link:
				painter.save()
				selected_rect = QRectF(x, y, w, lbl_rect.height()+app_constants.THUMB_H_SIZE)
				painter.setPen(Qt.NoPen)
				painter.setBrush(QBrush(QColor(255,0,0,120)))
				p_path = QPainterPath()
				p_path.setFillRule(Qt.WindingFill)
				p_path.addRoundedRect(selected_rect, 5,5)
				p_path.addRect(x,y, 20, 20)
				p_path.addRect(x+w-20,y, 20, 20)
				painter.drawPath(p_path.simplified())
				#painter.fillRect(selected_rect, QColor(164,164,164,120))
				painter.restore()

			if app_constants.DEBUG:
				painter.save()
				painter.setBrush(QBrush(QColor("red")))
				painter.setPen(QColor("white"))
				txt_l = self.title_font_m.width(str(gallery.id))
				painter.drawRect(x, y, txt_l*2, self.title_font_m.height())
				painter.drawText(x+1, y+11, str(gallery.id))
				painter.restore()
			#if option.state & QStyle.State_Selected:
			#	painter.setPen(QPen(option.palette.highlightedText().color()))
		else:
			super().paint(painter, option, index)

	def sizeHint(self, option, index):
		return QSize(self.W, self.H)

class MangaTableView(QListView):
	"""
	"""
	STATUS_BAR_MSG = pyqtSignal(str)
	SERIES_DIALOG = pyqtSignal()

	def __init__(self, parent=None):
		super().__init__(parent)
		self.parent_widget = parent
		self.setViewMode(self.IconMode)
		#self.H = app_constants.GRIDBOX_H_SIZE
		#self.W = app_constants.GRIDBOX_W_SIZE + (app_constants.SIZE_FACTOR//5)
		self.setResizeMode(self.Adjust)
		#self.setIconSize(QSize(app_constants.THUMB_W_SIZE-app_constants.SIZE_FACTOR,
		#				 app_constants.THUMB_H_SIZE-app_constants.SIZE_FACTOR))
		# all items have the same size (perfomance)
		#self.setUniformItemSizes(True)
		# improve scrolling
		self.setVerticalScrollMode(self.ScrollPerPixel)
		self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.setLayoutMode(self.SinglePass)
		self.setMouseTracking(True)
		#self.sort_model = SortFilterModel()
		#self.sort_model.setDynamicSortFilter(True)
		#self.sort_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
		#self.sort_model.setSortLocaleAware(True)
		#self.sort_model.setSortCaseSensitivity(Qt.CaseInsensitive)
		self.manga_delegate = ListDelegate(parent)
		self.setItemDelegate(self.manga_delegate)
		self.setSelectionBehavior(self.SelectItems)
		self.setSelectionMode(self.ExtendedSelection)
		#self.gallery_model = GalleryModel(parent)
		#self.gallery_model.db_emitter.DONE.connect(self.sort_model.setup_search)
		#self.sort_model.change_model(self.gallery_model)
		#self.sort_model.sort(0)
		#self.sort_model.ROWCOUNT_CHANGE.connect(self.gallery_model.ROWCOUNT_CHANGE.emit)
		#self.setModel(self.sort_model)
		#self.SERIES_DIALOG.connect(self.spawn_dialog)
		self.doubleClicked.connect(lambda idx: idx.data(Qt.UserRole+1).chapters[0].open())
		self.setViewportMargins(0,0,0,0)

		self.gallery_window = misc.GalleryMetaWindow(parent if parent else self)
		self.gallery_window.arrow_size = (10,10,)
		self.clicked.connect(lambda idx: self.gallery_window.show_gallery(idx, self))

		self.current_sort = app_constants.CURRENT_SORT
		#self.sort(self.current_sort)
		if app_constants.DEBUG:
			def debug_print(a):
				try:
					print(a.data(Qt.UserRole+1))
				except:
					print("{}".format(a.data(Qt.UserRole+1)).encode(errors='ignore'))

			self.clicked.connect(debug_print)

		self.k_scroller = QScroller.scroller(self)

	def resizeEvent(self, event):
		from PyQt5.QtGui import QResizeEvent
		width = event.size().width()
		if width >= app_constants.LISTBOX_W_SIZE:
			possible = self.width()//app_constants.LISTBOX_W_SIZE
			print(possible)
			new_width = self.width()//possible-9 # 9 because.. reasons

			self.manga_delegate.dynamic_width = new_width
			#self.setGridSize(QSize(new_width, app_constants.LISTBOX_H_SIZE))
			#self.setIconSize(QSize(new_width, app_constants.LISTBOX_H_SIZE))
		else:
			self.manga_delegate.dynamic_width = width
			#self.setGridSize(QSize(width, app_constants.LISTBOX_H_SIZE))

		return super().resizeEvent(event)


class MangaView(QListView):
	"""
	Grid View
	"""

	STATUS_BAR_MSG = pyqtSignal(str)
	SERIES_DIALOG = pyqtSignal()

	def __init__(self, parent=None):
		super().__init__(parent)
		self.parent_widget = parent
		self.setViewMode(self.IconMode)
		self.H = app_constants.GRIDBOX_H_SIZE
		self.W = app_constants.GRIDBOX_W_SIZE + (app_constants.SIZE_FACTOR//5)
		self.setGridSize(QSize(self.W, self.H))
		self.setResizeMode(self.Adjust)
		self.setIconSize(QSize(app_constants.THUMB_W_SIZE,
						 app_constants.THUMB_H_SIZE))
		# all items have the same size (perfomance)
		self.setUniformItemSizes(True)
		# improve scrolling
		self.setVerticalScrollMode(self.ScrollPerPixel)
		self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.setLayoutMode(self.SinglePass)
		self.setMouseTracking(True)
		self.sort_model = SortFilterModel()
		self.sort_model.setDynamicSortFilter(True)
		self.sort_model.setFilterCaseSensitivity(Qt.CaseInsensitive)
		self.sort_model.setSortLocaleAware(True)
		self.sort_model.setSortCaseSensitivity(Qt.CaseInsensitive)
		self.manga_delegate = GridDelegate(parent)
		self.setItemDelegate(self.manga_delegate)
		self.setSelectionBehavior(self.SelectItems)
		self.setSelectionMode(self.ExtendedSelection)
		self.gallery_model = GalleryModel(parent)
		self.gallery_model.db_emitter.DONE.connect(self.sort_model.setup_search)
		self.sort_model.change_model(self.gallery_model)
		self.sort_model.sort(0)
		self.sort_model.ROWCOUNT_CHANGE.connect(self.gallery_model.ROWCOUNT_CHANGE.emit)
		self.setModel(self.sort_model)
		self.SERIES_DIALOG.connect(self.spawn_dialog)
		self.doubleClicked.connect(lambda idx: idx.data(Qt.UserRole+1).chapters[0].open())
		self.setViewportMargins(0,0,0,0)

		self.gallery_window = misc.GalleryMetaWindow(parent if parent else self)
		self.gallery_window.arrow_size = (10,10,)
		self.clicked.connect(lambda idx: self.gallery_window.show_gallery(idx, self))

		self.current_sort = app_constants.CURRENT_SORT
		self.sort(self.current_sort)
		if app_constants.DEBUG:
			def debug_print(a):
				try:
					print(a.data(Qt.UserRole+1))
				except:
					print("{}".format(a.data(Qt.UserRole+1)).encode(errors='ignore'))

			self.clicked.connect(debug_print)

		self.k_scroller = QScroller.scroller(self)

	def get_visible_indexes(self, column=0):
		"find all galleries in viewport"
		gridW = self.W
		gridH = self.H
		region = self.viewport().visibleRegion()
		idx_found = []

		def idx_is_visible(idx):
			idx_rect = self.visualRect(idx)
			return region.contains(idx_rect) or region.intersects(idx_rect)

		#get first index
		first_idx = self.indexAt(QPoint(gridW//2, 0)) # to get indexes on the way out of view
		if not first_idx.isValid():
			first_idx = self.indexAt(QPoint(gridW//2, gridH//2))

		if first_idx.isValid():
			nxt_idx = first_idx
			# now traverse items until index isn't visible
			while(idx_is_visible(nxt_idx)):
				idx_found.append(nxt_idx)
				nxt_idx = nxt_idx.sibling(nxt_idx.row()+1, column)
			
		return idx_found

	def wheelEvent(self, event):
		if self.gallery_window.isVisible():
			self.gallery_window.hide_animation.start()
		return super().wheelEvent(event)

	def mouseMoveEvent(self, event):
		self.gallery_window.mouseMoveEvent(event)
		return super().mouseMoveEvent(event)

	def keyPressEvent(self, event):
		if event.key() == Qt.Key_Return:
			s_idx = self.selectedIndexes()
			if s_idx:
				for idx in s_idx:
					self.doubleClicked.emit(idx)
		return super().keyPressEvent(event)

	def remove_gallery(self, index_list, local=False):
		self.sort_model.setDynamicSortFilter(False)
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
			log_i('Removing {} galleries'.format(len(index_list)))
			self.gallery_model.REMOVING_ROWS = True
			for index in index_list:
				gallery = index.data(Qt.UserRole+1)
				gallery_list.append(gallery)
				log_i('Attempt to remove: {} by {}'.format(gallery.title.encode(),
											gallery.artist.encode()))
			gallerydb.add_method_queue(gallerydb.GalleryDB.del_gallery, True, gallery_list, local=local)
			rows = sorted([x.row() for x in index_list])

			for x in range(len(rows), 0, -1):
				self.sort_model.removeRows(rows[x-1])
			self.STATUS_BAR_MSG.emit('Gallery removed!')
			self.gallery_model.REMOVING_ROWS = False
		self.sort_model.setDynamicSortFilter(True)

	def favorite(self, index):
		assert isinstance(index, QModelIndex)
		gallery = index.data(Qt.UserRole+1)
		if gallery.fav == 1:
			gallery.fav = 0
			#self.model().replaceRows([gallery], index.row(), 1, index)
			gallerydb.add_method_queue(gallerydb.GalleryDB.modify_gallery, True, gallery.id, {'fav':0})
			self.gallery_model.CUSTOM_STATUS_MSG.emit("Unfavorited")
		else:
			gallery.fav = 1
			#self.model().replaceRows([gallery], index.row(), 1, index)
			gallerydb.add_method_queue(gallerydb.GalleryDB.modify_gallery, True, gallery.id, {'fav':1})
			self.gallery_model.CUSTOM_STATUS_MSG.emit("Favorited")

	def duplicate_check(self, simple=True):
		mode = 'simple' if simple else 'advanced'
		log_i('Checking for duplicates in mode: {}'.format(mode))
		notifbar = self.parent_widget.notification_bar
		notifbar.add_text('Checking for duplicates...')
		if simple:
			galleries = self.gallery_model._data.copy()
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

				class GalleryContextMenu(QMenu):
					app_inst = self.parent_widget
					viewer = self
					def __init__(self, parent=None):
						super().__init__(parent)
						show_in_library_act = self.addAction('Show in library')
						show_in_library_act.triggered.connect(self.show_in_library)
						delete_gallery = self.addAction('Remove gallery')
						delete_gallery.triggered.connect(self.delete_gallery)
						delete_gallery_source = self.addAction("Remove gallery and it's files")
						delete_gallery_source.triggered.connect(lambda: self.delete_gallery(True))

					def show_in_library(self):
						index = CommonView.find_index(self.viewer, self.gallery_widget.gallery.id, True)
						if index:
							CommonView.scroll_to_index(self.viewer, index)
							self.app_inst.manga_table_view.scroll_to_index(index)

					def delete_gallery(self, source=False):
						index = CommonView.find_index(self.viewer, self.gallery_widget.gallery.id, True)
						if index and index.isValid():
							self.viewer.remove_gallery([index], source)
							if self.gallery_widget.parent_widget.gallery_layout.count() == 1:
								self.gallery_widget.parent_widget.close()
							else:
								self.gallery_widget.close()

				g_widget = io_misc.GalleryPopup(("These galleries are found to"+
										  " be duplicates.", duplicates), self.parentWidget(), menu=GalleryContextMenu())
				if g_widget.graphics_blur:
					g_widget.graphics_blur.setEnabled(False)
				buttons = g_widget.add_buttons("Close")
				buttons[0].clicked.connect(g_widget.close)
			else:
				notifbar.add_text('No duplicates found!')

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
		elif name == 'times_read':
			self.sort_model.setSortRole(Qt.UserRole+6)
			self.sort_model.sort(0, Qt.DescendingOrder)
			self.current_sort = 'times_read'

	def contextMenuEvent(self, event):
		handled = False
		index = self.indexAt(event.pos())
		index = self.sort_model.mapToSource(index)

		if index.data(Qt.UserRole+1) and index.data(Qt.UserRole+1).state == GridDelegate.G_DOWNLOAD:
			event.ignore()
			return

		selected = False
		s_indexes = self.selectedIndexes()
		select_indexes = []
		for idx in s_indexes:
			if idx.isValid() and idx.column() == 0:
				if not idx.data(Qt.UserRole+1).state == GridDelegate.G_DOWNLOAD:
					select_indexes.append(self.sort_model.mapToSource(idx))
		if len(select_indexes) > 1:
			selected = True

		if index.isValid():
			if self.gallery_window.isVisible():
				self.gallery_window.hide_animation.start()
			self.manga_delegate.CONTEXT_ON = True
			if selected:
				menu = misc.GalleryMenu(self, index, self.gallery_model,
							   self.parent_widget, select_indexes)
			else:
				menu = misc.GalleryMenu(self, index, self.gallery_model,
							   self.parent_widget)
			handled = True

		if handled:
			menu.exec_(event.globalPos())
			self.manga_delegate.CONTEXT_ON = False
			event.accept()
			del menu
		else:
			event.ignore()

	# TODO: move to CommonView
	def replace_edit_gallery(self, list_of_gallery, pos=None, db_optimize=True):
		"Replaces the view and DB with given list of gallery, at given position"
		assert isinstance(list_of_gallery, (list, gallerydb.Gallery)), "Please pass a gallery to replace with"
		if isinstance(list_of_gallery, gallerydb.Gallery):
			list_of_gallery = [list_of_gallery]
		log_d('Replacing {} galleries'.format(len(list_of_gallery)))
		if db_optimize:
			gallerydb.GalleryDB.begin()
		for gallery in list_of_gallery:
			if not pos:
				index = CommonView.find_index(self, gallery.id)
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
			 'chapters':gallery.chapters,
			 'exed':gallery.exed}

			gallerydb.add_method_queue(gallerydb.GalleryDB.modify_gallery,
							 True, gallery.id, **kwdict)
		if db_optimize:
			gallerydb.add_method_queue(gallerydb.GalleryDB.end, True)
		assert isinstance(pos, int)
		self.gallery_model.replaceRows([gallery], pos, len(list_of_gallery))

	def spawn_dialog(self, index=False):
		if not index:
			dialog = gallerydialog.GalleryDialog(self.parent_widget)
			def add_to_model(g_list):
				self.sort_model.addRows(g_list)
				self.sort_model.init_search(self.sort_model.current_term)
			dialog.SERIES.connect(add_to_model)
			dialog.SERIES.connect(lambda: self.sort_model.init_search(self.sort_model.current_term))
		else:
			dialog = gallerydialog.GalleryDialog(self.parent_widget, [index])
			dialog.SERIES_EDIT.connect(self.replace_edit_gallery)
		
		dialog.show()

	def updateGeometries(self):
		super().updateGeometries()
		self.verticalScrollBar().setSingleStep(app_constants.SCROLL_SPEED)

#class MangaTableView(QTableView):
#	STATUS_BAR_MSG = pyqtSignal(str)
#	SERIES_DIALOG = pyqtSignal()

#	def __init__(self, parent=None):
#		super().__init__(parent)
#		# options
#		self.parent_widget = parent
#		self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
#		self.setSelectionBehavior(self.SelectRows)
#		self.setSelectionMode(self.ExtendedSelection)
#		self.setShowGrid(True)
#		self.setSortingEnabled(True)
#		h_header = self.horizontalHeader()
#		h_header.setSortIndicatorShown(True)
#		v_header = self.verticalHeader()
#		v_header.sectionResizeMode(QHeaderView.Fixed)
#		v_header.setDefaultSectionSize(24)
#		v_header.hide()
#		palette = self.palette()
#		palette.setColor(palette.Highlight, QColor(88, 88, 88, 70))
#		palette.setColor(palette.HighlightedText, QColor('black'))
#		self.setPalette(palette)
#		self.setIconSize(QSize(0,0))
#		self.doubleClicked.connect(lambda idx: idx.data(Qt.UserRole+1).chapters[0].open())
#		self.grabGesture(Qt.SwipeGesture)
#		self.k_scroller = QScroller.scroller(self)

#	# display tooltip only for elided text
#	#def viewportEvent(self, event):
#	#	if event.type() == QEvent.ToolTip:
#	#		h_event = QHelpEvent(event)
#	#		index = self.indexAt(h_event.pos())
#	#		if index.isValid():
#	#			size_hint = self.itemDelegate(index).sizeHint(self.viewOptions(),
#	#											  index)
#	#			rect = QRect(0, 0, size_hint.width(), size_hint.height())
#	#			rect_visual = self.visualRect(index)
#	#			if rect.width() <= rect_visual.width():
#	#				QToolTip.hideText()
#	#				return True
#	#	return super().viewportEvent(event)

#	def keyPressEvent(self, event):
#		if event.key() == Qt.Key_Return:
#			s_idx = self.selectionModel().selectedRows()
#			if s_idx:
#				for idx in s_idx:
#					self.doubleClicked.emit(idx)
#		return super().keyPressEvent(event)

#	def remove_gallery(self, index_list, local=False):
#		self.parent_widget.manga_list_view.remove_gallery(index_list, local)

#	def contextMenuEvent(self, event):
#		handled = False
#		index = self.indexAt(event.pos())
#		index = self.sort_model.mapToSource(index)

#		if index.data(Qt.UserRole+1) and index.data(Qt.UserRole+1).state == CustomDelegate.G_DOWNLOAD:
#			event.ignore()
#			return

#		selected = False
#		s_indexes = self.selectionModel().selectedRows()
#		select_indexes = []
#		for idx in s_indexes:
#			if idx.isValid():
#				if not idx.data(Qt.UserRole+1).state == CustomDelegate.G_DOWNLOAD:
#					select_indexes.append(self.sort_model.mapToSource(idx))
#		if len(select_indexes) > 1:
#			selected = True

#		if index.isValid():
#			if selected:
#				menu = misc.GalleryMenu(self, 
#							index,
#							self.parent_widget.manga_list_view.gallery_model,
#							self.parent_widget, select_indexes)
#			else:
#				menu = misc.GalleryMenu(self, index, self.gallery_model,
#							   self.parent_widget)
#			handled = True

#		if handled:
#			menu.exec_(event.globalPos())
#			event.accept()
#			del menu
#		else:
#			event.ignore()

class CommonView:
	"""
	Contains identical view implentations
	"""
	@staticmethod
	def find_index(view_cls, gallery_id, sort_model=False):
		"Finds and returns the index associated with the gallery id"
		index = None
		model = view_cls.sort_model if sort_model else view_cls.gallery_model
		rows = model.rowCount()
		for r in range(rows):
			indx = model.index(r, 0)
			m_gallery = indx.data(Qt.UserRole+1)
			if m_gallery.id == gallery_id:
				index = indx
				break
		return index

	@staticmethod
	def open_random_gallery(view_cls):
		g = random.randint(0, view_cls.sort_model.rowCount()-1)
		indx = view_cls.sort_model.index(g, 1)
		chap_numb = 0
		if app_constants.OPEN_RANDOM_GALLERY_CHAPTERS:
			gallery = indx.data(Qt.UserRole+1)
			b = len(gallery.chapters)
			if b > 1:
				chap_numb = random.randint(0, b-1)

		CommonView.scroll_to_index(view_cls, view_cls.sort_model.index(indx.row(), 0))
		indx.data(Qt.UserRole+1).chapters[chap_numb].open()

	@staticmethod
	def scroll_to_index(view_cls, idx, select=True):
		old_value = view_cls.verticalScrollBar().value()
		view_cls.setUpdatesEnabled(False)
		view_cls.verticalScrollBar().setValue(0)
		idx_rect = view_cls.visualRect(idx)
		view_cls.verticalScrollBar().setValue(old_value)
		view_cls.setUpdatesEnabled(True)
		rect = QRectF(idx_rect)
		if app_constants.DEBUG:
			print("Scrolling to index:", rect.getRect())
		view_cls.k_scroller.ensureVisible(rect, 0, 0)
		if select:
			view_cls.setCurrentIndex(idx)

if __name__ == '__main__':
	raise NotImplementedError("Unit testing not yet implemented")
