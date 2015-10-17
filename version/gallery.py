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

class GalleryMetaPopup(QFrame):
	def __init__(self, parent):
		super().__init__(parent, Qt.Window | Qt.FramelessWindowHint)
		self.setFrameShape(QFrame.NoFrame)
		self.setAttribute(Qt.WA_ShowWithoutActivating)
		self.setAttribute(Qt.WA_DeleteOnClose)
		self.initUI()
		#self.resize(gui_constants.POPUP_WIDTH,gui_constants.POPUP_HEIGHT)
		self.setFixedWidth(gui_constants.POPUP_WIDTH)
		self.setMaximumHeight(gui_constants.POPUP_HEIGHT)
		self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
		self.parent_widget = parent
	
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

		self.tags_lbl = QLabel("Tags:")
		self.tags_scroll = QScrollArea()
		self.tags_scroll.setFrameStyle(QFrame.NoFrame)
		self.tag_widget = QWidget(self)
		self.tags_scroll.setWidget(self.tag_widget)
		self.tags_scroll.setWidgetResizable(True)
		self.tags_scroll.setSizePolicy(QSizePolicy.MinimumExpanding,
								 QSizePolicy.MinimumExpanding)
		self.tags = QFormLayout(self.tag_widget)


		self.pub_date = QLabel()
		self.date_added = QLabel()

		link_lbl = QLabel("Link:")
		self.link = misc.ClickedLabel()
		self.link.setWordWrap(True)
		self.link.clicked.connect(lambda: utils.open_web_link(self.link.text()))

		form_l.addRow(self.title_lbl, self.title)
		form_l.addRow(self.artist_lbl, self.artist)
		form_l.addRow(self.chapters_lbl, self.chapters)
		form_l.addRow(self.info_lbl, self.info)
		form_l.addRow(lang_lbl, self.lang)
		form_l.addRow(self.tags_lbl, self.tags_scroll)
		form_l.addRow(link_lbl, self.link)

	def set_gallery(self, gallery):
		def has_tags(tags):
			t_len = len(tags)
			if not t_len:
				return False
			if t_len == 1:
				if 'default' in tags:
					if not tags['default']:
						return False
			return True

		if has_tags(gallery.tags):
			self.tags_scroll.show()
			ns_layout = QFormLayout()
			self.tags.addRow(ns_layout)
			for namespace in gallery.tags:
				tags_lbls = misc.FlowLayout()
				if namespace == 'default':
					self.tags.insertRow(0, tags_lbls)
				else:
					self.tags.addRow(namespace, tags_lbls)

				for n, tag in enumerate(gallery.tags[namespace], 1):
					if namespace == 'default':
						t = misc.TagText(search_widget=self.parent_widget)
					else:
						t = misc.TagText(search_widget=self.parent_widget,
					   namespace=namespace)
					t.setText(tag)
					tags_lbls.addWidget(t)
		else:
			self.tags_scroll.hide()
		self.tag_widget.adjustSize()

		self.title.setText(gallery.title)
		self.artist.setText(gallery.artist)
		self.chapters.setText("{}".format(len(gallery.chapters)))
		self.info.setText(gallery.info)
		self.lang.setText(gallery.language)
		self.type.setText(gallery.type)
		self.status.setText(gallery.status)
		self.link.setText(gallery.link)
		self.adjustSize()

	def hideEvent(self, event):
		misc.clearLayout(self.tags)
		return super().hideEvent(event)

class GallerySearch(QObject):
	FINISHED = pyqtSignal()
	def __init__(self, data):
		super().__init__()
		self._data = data
		self.result = {}
		# filtering
		self.fav = False
		self.tags = {}
		self.title = ""
		self.artist = ""
		self.other = ""
		self.excludes = []
		self.allow_all = False # to make it easier

	def set_data(self, new_data):
		self._data = new_data
		self.result = {g.id: True for g in self._data}

	def set_fav(self, new_fav):
		self.fav = new_fav

	def test(self):
		self.result.clear()
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

		for gallery in self._data:
			allow = False
			if self.fav:
				if gallery.fav == 1:
					s = do_search()
					if s:
						allow = return_searched(s)
					else: allow = True
					if self.allow_all: # allowing all FAVS
						allow = True
			else:
				s = do_search()
				if s:
					allow = return_searched(s)
				else: allow = True
				if self.allow_all:
					allow = True
			self.result[gallery.id] = allow

	def search(self, term):
		term = ' '.join(term.lower().split())
		if not gui_constants.ALLOW_SEARCH_REGEX:
			remove = '^$*+?{}\\|()[]'
			for x in remove:
				if x == '[' or x == ']':
					continue
				else:
					term = term.replace(x, '.')
		else:
			try:
				regex.compile(term)
			except regex.error:
				return

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
			if 'title:' in term:
				t = regex.search('(?<=title:)"([^"]*)"', term)
				if t:
					n = t.group()
					term = term.replace('title:'+n, '')
					t = n.replace('"', '')
					self.title = [t]
			else:
				self.title = trim_for_non_tag(term)

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

			self.tags = utils.tag_to_dict(term)
		else:
			self.allow_all = True

		self.test()
		self.FINISHED.emit()

	#def search(self, term):
	#	term = ' '.join(term.lower().split())
	#	terms = utils.get_terms(term)
	#	self.excludes = []

	#	def remove_abs_terms(term):
	#		if term.startswith(('title:')):
	#			term = term[6:]
	#		elif term.startswith(('artist:')):
	#			term = term[7:]
	#		return term
	#	d_terms = {}
	#	# get excludes, title, artist
	#	for t in terms:
	#		if t[0] == '-':
	#			term = t[1:]
	#			self.excludes.append(remove_abs_terms(term))
	#			continue
	#		if t.startswith('title:'):
	#			term = t[6:]
	#			self.title = term
	#			continue
	#		if t.startswith('artist:'):
	#			term = t[7:]
	#			self.artist = term
	#			continue

	#		d_terms[t] = False

	#def s_text(self, list_of_text, text_to_test):
	#	valid = []
	#	text = text_to_test.lower()
	#	for t in list_of_text:
	#		t = t.lower()
	#		if t in text:
	#			valid.append(True)
	#		else:
	#			valid.append(False)
	#	if valid and all(valid):
	#		return True
	#	else:
	#		return False

	#def s_tags(self, tags, excludes):
	#	return True

class SortFilterModel(QSortFilterProxyModel):
	ROWCOUNT_CHANGE = pyqtSignal()
	_DO_SEARCH = pyqtSignal(str)
	_CHANGE_SEARCH_DATA = pyqtSignal(list)
	_CHANGE_FAV = pyqtSignal(bool)

	HISTORY_SEARCH_TERM = pyqtSignal(str)
	# Navigate terms
	NEXT, PREV = range(2)

	def __init__(self, parent=None):
		super().__init__(parent)
		self._data = gui_constants.GALLERY_DATA
		self._search_ready = False
		self.current_term = ''
		self.terms_history = []
		self.current_term_history = 0

	def navigate_history(self, direction=PREV):
		print(self.terms_history)
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
		print(new_term)
		return new_term


	def fetchMore(self, index):
		return super().fetchMore(index)

	def fav_view(self):
		self._CHANGE_FAV.emit(True)
		self._DO_SEARCH.emit('')

	def catalog_view(self):
		self._CHANGE_FAV.emit(False)
		self._DO_SEARCH.emit('')

	def setup_search(self):
		if not self._search_ready:
			self.gallery_search = GallerySearch(self._data)
			self.gallery_search.FINISHED.connect(self.invalidateFilter)
			self.gallery_search.FINISHED.connect(lambda: self.ROWCOUNT_CHANGE.emit())
			self.search_thread = QThread()
			self.gallery_search.moveToThread(self.search_thread)
			self.search_thread.start()
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
	_data = gui_constants.GALLERY_DATA

	REMOVING_ROWS = False

	def __init__(self, parent=None):
		super().__init__(parent)
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
			return bg_color

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

		if role == Qt.UserRole+6:
			return current_gallery.times_read

		return None

	def rowCount(self, index = QModelIndex()):
		if not index.isValid():
			#print(self._data_count)
			return self._data_count
		else:
			return 0

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
		for gallery in list_of_gallery:
			gallerydb.add_method_queue(gallerydb.GalleryDB.add_gallery_return, True, gallery)
			gallery.profile = gallerydb.PROFILE_TO_MODEL.get()
			self._data.insert(position, gallery)
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
		for pos, gallery in enumerate(list_of_gallery, 1):
			self._data.append(gallery)
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
	"A custom delegate for the model/view framework"

	POPUP = pyqtSignal()
	CONTEXT_ON = False

	# Gallery states
	G_NORMAL, G_DOWNLOAD = range(2)

	def __init__(self, parent=None):
		super().__init__()
		QPixmapCache.setCacheLimit(gui_constants.THUMBNAIL_CACHE_SIZE[0]*
							 gui_constants.THUMBNAIL_CACHE_SIZE[1])
		self.popup_window = GalleryMetaPopup(parent)
		self.popup_timer = QTimer()
		self._painted_indexes = {}

		#misc.FileIcon.refresh_default_icon()
		self.file_icons = misc.FileIcon()
		if gui_constants.USE_EXTERNAL_VIEWER:
			self.external_icon = self.file_icons.get_external_file_icon()
		else:
			self.external_icon = self.file_icons.get_default_file_icon()

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
			def center_img(width):
				new_x = x
				if width < w:
					diff = w - width
					offset = diff//2
					new_x += offset
				return new_x
			# if we can't find a cached image
			pix_cache = QPixmapCache.find(self.key(gallery.profile))
			if isinstance(pix_cache, QPixmap):
				self.image = pix_cache
				img_x = center_img(self.image.width())
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
				if self.image.height() < self.image.width(): #to keep aspect ratio
					painter.drawPixmap(QPoint(img_x,y),
							self.image)
				else:
					painter.drawPixmap(QPoint(img_x,y),
							self.image)

			# draw star if it's favorited
			if gallery.fav == 1:
				painter.drawPixmap(QPointF(x,y), QPixmap(gui_constants.STAR_PATH))
			
			if gui_constants._REFRESH_EXTERNAL_VIEWER:
				if gui_constants.USE_EXTERNAL_VIEWER:
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
				if gui_constants.DISPLAY_GALLERY_TYPE:
					self.type_icon = self.file_icons.get_file_icon(gallery.path)
					if self.type_icon and not self.type_icon.isNull():
						self.type_icon.paint(painter, QRect(x+2, y+gui_constants.THUMB_H_SIZE-16, 16, 16))

				if gui_constants.USE_EXTERNAL_PROG_ICO:
					if self.external_icon and not self.external_icon.isNull():
						self.external_icon.paint(painter, QRect(x+w-30, y+gui_constants.THUMB_H_SIZE-28, 28, 28))

			def draw_text_label(lbl_h):
				#draw the label for text
				painter.save()
				painter.translate(x, y+gui_constants.THUMB_H_SIZE)
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

				if gui_constants.GALLERY_FONT_ELIDE:
					lbl_rect = draw_text_label(min(t_h+a_h+3, gui_constants.GRIDBOX_LBL_H))
				else:
					lbl_rect = draw_text_label(gui_constants.GRIDBOX_LBL_H)

				clipping = QRectF(x, y+gui_constants.THUMB_H_SIZE, w, gui_constants.GRIDBOX_LBL_H - 10)
				title_layout.draw(painter, QPointF(x, y+gui_constants.THUMB_H_SIZE),
					  clip=clipping)
				artist_layout.draw(painter, QPointF(x, y+gui_constants.THUMB_H_SIZE+t_h),
					   clip=clipping)
				#painter.fillRect(option.rect, QColor)
			else:
				if gui_constants.GALLERY_FONT_ELIDE:
					lbl_rect = draw_text_label(self.text_label_h)
				else:
					lbl_rect = draw_text_label(gui_constants.GRIDBOX_LBL_H)
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
				if not self.popup_window.underMouse():
					self.popup_window.hide()

			if option.state & QStyle.State_Selected:
				painter.save()
				selected_rect = QRectF(x, y, w, lbl_rect.height()+gui_constants.THUMB_H_SIZE)
				painter.setPen(Qt.NoPen)
				painter.setBrush(QBrush(QColor(164,164,164,120)))
				p_path = QPainterPath()
				p_path.setFillRule(Qt.WindingFill)
				p_path.addRoundedRect(selected_rect, 5,5)
				p_path.addRect(x,y, 20, 20)
				p_path.addRect(x+w-20,y, 20, 20)
				painter.drawPath(p_path.simplified())
				#painter.fillRect(selected_rect, QColor(164,164,164,120))
				painter.restore()

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
		self.setSelectionBehavior(self.SelectItems)
		self.setSelectionMode(self.ExtendedSelection)
		self.gallery_model = GalleryModel(parent)
		self.gallery_model.db_emitter.DONE.connect(self.sort_model.setup_search)
		self.sort_model.change_model(self.gallery_model)
		self.sort_model.sort(0)
		self.sort_model.ROWCOUNT_CHANGE.connect(self.gallery_model.ROWCOUNT_CHANGE.emit)
		self.setModel(self.sort_model)
		self.SERIES_DIALOG.connect(self.spawn_dialog)
		self.doubleClicked.connect(self.open_chapter)
		self.setViewportMargins(0,0,0,0)
		self.current_sort = gui_constants.CURRENT_SORT
		self.sort(self.current_sort)
		if gui_constants.DEBUG:
			def debug_print(a):
				pass
				#print(a.data(Qt.UserRole+1))

			self.clicked.connect(debug_print)

		#self.viewport().grabGesture(Qt.SwipeGesture)
		self.k_scroller = QScroller.scroller(self)
		#self.k_scroller = QScroller.scroller(self)
		#self.k_scroller.grabGesture(self)
		#self._scroll_pos = QPoint()
	#	self.ti = QTimer()
	#	self.ti.timeout.connect(self.test_)
	#	self.ti.start(5000)

	def scroll_to_index(self, idx, select=True):
		rect = self.visualRect(idx)
		self.k_scroller.ensureVisible(QRectF(rect), 0, 0)
		if select:
			self.setCurrentIndex(idx)

	# unusable code
	def event(self, event):
		#if event.type() == QEvent.ToolTip:
		#	help_event = QHelpEvent(event)
		#	index = self.indexAt(help_event.globalPos())
		#	if index is not -1:
		#		QToolTip.showText(help_event.globalPos(), "Tooltip!")
		#	else:
		#		QToolTip().hideText()
		#		event.ignore()
		#	return True

		if event.type() == QEvent.Gesture:
			print("yes!")
		else:
			return super().event(event)

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
		if gui_constants.OPEN_RANDOM_GALLERY_CHAPTERS:
			gallery = indx.data(Qt.UserRole+1)
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
						index = self.viewer.find_index(self.gallery_widget.gallery.id, True)
						if index:
							self.viewer.scroll_to_index(index)
							self.app_inst.manga_table_view.scroll_to_index(index)

					def delete_gallery(self, source=False):
						index = self.viewer.find_index(self.gallery_widget.gallery.id)
						if index and index.isValid():
							self.viewer.remove_gallery([index], source)
							if self.gallery_widget.parent_widget.gallery_layout.count() == 1:
								self.gallery_widget.parent_widget.close()
							else:
								self.gallery_widget.close()

				g_widget = file_misc.GalleryPopup(("These galleries are found to"+
										  " be duplicates.", duplicates), self.parentWidget(), menu=GalleryContextMenu())
				g_widget.graphics_blur.setEnabled(False)
				buttons = g_widget.add_buttons("Close")
				buttons[0].clicked.connect(g_widget.close)
			else:
				notifbar.add_text('No duplicates found!')

	def open_chapter(self, index, chap_numb=0):
		if not isinstance(index, list):
			index = [index]
		for x in index:
			gallery = x.data(Qt.UserRole+1)
			if gallery.state == CustomDelegate.G_DOWNLOAD:
				continue
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
		elif name == 'times_read':
			self.sort_model.setSortRole(Qt.UserRole+6)
			self.sort_model.sort(0, Qt.DescendingOrder)
			self.current_sort = 'times_read'

	def contextMenuEvent(self, event):
		handled = False
		index = self.indexAt(event.pos())
		index = self.sort_model.mapToSource(index)

		if index.data(Qt.UserRole+1) and index.data(Qt.UserRole+1).state == CustomDelegate.G_DOWNLOAD:
			event.ignore()
			return

		selected = False
		s_indexes = self.selectedIndexes()
		select_indexes = []
		for idx in s_indexes:
			if idx.isValid() and idx.column() == 0:
				if not idx.data(Qt.UserRole+1).state == CustomDelegate.G_DOWNLOAD:
					select_indexes.append(self.sort_model.mapToSource(idx))
		if len(select_indexes) > 1:
			selected = True

		if index.isValid():
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

	#need this for debugging purposes
	def resizeEvent(self, resizeevent):
		super().resizeEvent(resizeevent)
		#print(resizeevent.size())

	def find_index(self, gallery_id, sort_model=False):
		"Finds and returns the index associated with the gallery id"
		index = None
		model = self.sort_model if sort_model else self.gallery_model
		rows = model.rowCount()
		print(rows)
		for r in range(rows):
			indx = model.index(r, 0)
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
			dialog.SERIES.connect(self.sort_model.addRows)
			dialog.SERIES.connect(lambda: self.sort_model.init_search(self.sort_model.current_term))
		else:
			dialog = gallerydialog.GalleryDialog(self.parent_widget, [index])
			dialog.SERIES_EDIT.connect(self.replace_edit_gallery)
		
		dialog.show()

	def updateGeometries(self):
		super().updateGeometries()
		self.verticalScrollBar().setSingleStep(gui_constants.SCROLL_SPEED)

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
		self.grabGesture(Qt.SwipeGesture)
		self.k_scroller = QScroller.scroller(self)
		self.k_scroller.grabGesture(self, QScroller.TouchGesture)

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

	def scroll_to_index(self, idx, select=True):
		rect = self.visualRect(idx)
		self.k_scroller.ensureVisible(QRectF(rect), 0, 0)
		if select:
			self.selectRow(idx.row())

	def keyPressEvent(self, event):
		if event.key() == Qt.Key_Return:
			s_idx = self.selectionModel().selectedRows()
			if s_idx:
				for idx in s_idx:
					self.doubleClicked.emit(idx)
		return super().keyPressEvent(event)

	def remove_gallery(self, index_list, local=False):
		self.parent_widget.manga_list_view.remove_gallery(index_list, local)

	def contextMenuEvent(self, event):
		handled = False
		index = self.indexAt(event.pos())
		index = self.sort_model.mapToSource(index)

		if index.data(Qt.UserRole+1).state == CustomDelegate.G_DOWNLOAD:
			event.ignore()
			return

		selected = False
		s_indexes = self.selectionModel().selectedRows()
		select_indexes = []
		for idx in s_indexes:
			if idx.isValid():
				if not idx.data(Qt.UserRole+1).state == CustomDelegate.G_DOWNLOAD:
					select_indexes.append(self.sort_model.mapToSource(idx))
		if len(select_indexes) > 1:
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
