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

from PyQt5.QtWidgets import (QTreeWidget, QTreeWidgetItem, QWidget,
							 QVBoxLayout, QTabWidget, QAction, QGraphicsScene,
							 QSizePolicy, QMenu, QAction, QApplication,
							 QListWidget, QHBoxLayout, QPushButton, QStackedLayout,
							 QFrame, QSizePolicy, QListView, QFormLayout, QLineEdit,
							 QLabel, QStyledItemDelegate, QStyleOptionViewItem)
from PyQt5.QtCore import (Qt, QTimer, pyqtSignal, QRect, QSize, QEasingCurve,
						  QSortFilterProxyModel, QIdentityProxyModel, QModelIndex,
						  QPointF, QRectF)
from PyQt5.QtGui import QIcon, QStandardItem, QFont, QPainter, QColor, QBrush

import gallerydb
import app_constants
import utils
import misc

class NoTooltipModel(QIdentityProxyModel):

	def __init__(self, model, parent=None):
		super().__init__(parent)
		self.setSourceModel(model)

	def data(self, index, role = Qt.DisplayRole):
		if role == Qt.ToolTipRole:
			return None
		return self.sourceModel().data(index, role)

class UniqueInfoModel(QSortFilterProxyModel):
	def __init__(self, gallerymodel, role, parent=None):
		super().__init__(parent)
		self.setSourceModel(NoTooltipModel(gallerymodel, parent))
		self._unique = set()
		self._unique_role = role
		self.setDynamicSortFilter(True)

	def filterAcceptsRow(self, source_row, parent_index):
		if self.sourceModel():
			idx = self.sourceModel().index(source_row, 0, parent_index)
			if idx.isValid():
				unique = idx.data(self._unique_role)
				if unique:
					if not unique in self._unique:
						self._unique.add(unique)
						return True
		return False

class ListDelegate(QStyledItemDelegate):
	def __init__(self, parent=None):
		self.parent_widget = parent
		super().__init__(parent)
		self.create_new_list_txt = 'Create new list...'
	
	def sizeHint(self, option, index):
		size = super().sizeHint(option, index)
		if index.data(Qt.DisplayRole) == self.create_new_list_txt:
			return size
		return QSize(size.width(), size.height()*2)

class GalleryArtistsList(QListView):
	artist_clicked = pyqtSignal(str)

	def __init__(self, gallerymodel, parent=None):
		super().__init__(parent)
		self.g_artists_model = UniqueInfoModel(gallerymodel, gallerymodel.ARTIST_ROLE, self)
		self.setModel(self.g_artists_model)
		self.setModelColumn(app_constants.ARTIST)
		self.g_artists_model.setSortRole(gallerymodel.ARTIST_ROLE)
		self.g_artists_model.sort(0)
		self.doubleClicked.connect(self._artist_clicked)
		self.ARTIST_ROLE = gallerymodel.ARTIST_ROLE
		self.setItemDelegate(ListDelegate(self))

	def _artist_clicked(self, idx):
		if idx.isValid():
			self.artist_clicked.emit(idx.data(self.ARTIST_ROLE))

class TagsTreeView(QTreeWidget):
	TAG_SEARCH = pyqtSignal(str)
	NEW_LIST = pyqtSignal(str, gallerydb.GalleryList)
	def __init__(self, parent):
		super().__init__(parent)
		self.setSelectionBehavior(self.SelectItems)
		self.setSelectionMode(self.ExtendedSelection)
		self.clipboard = QApplication.clipboard()
		self.itemDoubleClicked.connect(lambda i: self.search_tags([i]) if i.parent() else None)

	def _convert_to_str(self, items):
		tags = {}
		d_tags = []
		for item in items:
			ns_item = item.parent()
			if ns_item.text(0) == 'No namespace':
				d_tags.append(item.text(0))
				continue
			if ns_item.text(0) in tags:
				tags[ns_item.text(0)].append(item.text(0))
			else:
				tags[ns_item.text(0)] = [item.text(0)]
			
		search_txt = utils.tag_to_string(tags)
		d_search_txt = ''
		for x, d_t in enumerate(d_tags, 1):
			if x == len(d_tags):
				d_search_txt += '{}'.format(d_t)
			else:
				d_search_txt += '{}, '.format(d_t)
		final_txt = search_txt + ', ' + d_search_txt if search_txt else d_search_txt
		return final_txt

	def search_tags(self, items):
		self.TAG_SEARCH.emit(self._convert_to_str(items))

	def create_list(self, items):
		g_list = gallerydb.GalleryList("New List", filter=self._convert_to_str(items))
		g_list.add_to_db()
		
		self.NEW_LIST.emit(g_list.name, g_list)

	def contextMenuEvent(self, event):
		handled = False
		selected = False
		s_items = self.selectedItems()

		if len(s_items) > 1:
			selected = True

		ns_count = 0
		for item in s_items:
			if not item.text(0).islower():
				ns_count += 1
		contains_ns =  True if ns_count > 0 else False

		def copy(with_ns=False):
			if with_ns:
				ns_item = s_items[0].parent()
				ns = ns_item.text(0)
				tag = s_items[0].text(0)
				txt = "{}:{}".format(ns, tag)
				self.clipboard.setText(txt)
			else:
				item = s_items[0]
				self.clipboard.setText(item.text(0))

		if s_items:
			menu = QMenu(self)
			if not selected:
				copy_act = menu.addAction('Copy')
				copy_act.triggered.connect(copy)
				if not contains_ns:
					if s_items[0].parent().text(0) != 'No namespace':
						copy_ns_act = menu.addAction('Copy with namespace')
						copy_ns_act.triggered.connect(lambda: copy(True))
			if not contains_ns:
				search_act = menu.addAction('Search')
				search_act.triggered.connect(lambda: self.search_tags(s_items))
				create_list_filter_act = menu.addAction('Create list with selected')
				create_list_filter_act.triggered.connect(lambda: self.create_list(s_items))
			handled = True

		if handled:
			menu.exec_(event.globalPos())
			event.accept()
			del menu
		else:
			event.ignore()

	def setup_tags(self):
		self.clear()
		tags = gallerydb.add_method_queue(gallerydb.TagDB.get_ns_tags, False)
		items = []
		for ns in tags:
			top_item = QTreeWidgetItem(self)
			if ns == 'default':
				top_item.setText(0, 'No namespace')
			else:
				top_item.setText(0, ns)
			for tag in tags[ns]:
				child_item = QTreeWidgetItem(top_item)
				child_item.setText(0, tag)
		self.sortItems(0, Qt.AscendingOrder)

class GalleryListEdit(misc.BasePopup):
	def __init__(self, gallery_list, item, parent):
		super().__init__(parent, blur=False)
		self.gallery_list = gallery_list
		self.item = item
		main_layout = QFormLayout(self.main_widget)
		self.name_edit = QLineEdit(gallery_list.name, self)
		main_layout.addRow("Name:", self.name_edit)
		self.filter_edit = QLineEdit(self)
		if gallery_list.filter:
			self.filter_edit.setText(gallery_list.filter)
		what_is_filter = misc.ClickedLabel("What is filter? (Hover)")
		what_is_filter.setToolTip(app_constants.WHAT_IS_FILTER)
		what_is_filter.setToolTipDuration(9999999999)
		main_layout.addRow(what_is_filter)
		main_layout.addRow("Filter", self.filter_edit)
		main_layout.addRow(self.buttons_layout)
		self.add_buttons("Close")[0].clicked.connect(self.close)
		self.add_buttons("Apply")[0].clicked.connect(self.accept)
		self.adjustSize()

	def accept(self):
		name = self.name_edit.text()
		self.item.setText(name)
		self.gallery_list.name = name
		self.gallery_list.filter = self.filter_edit.text()
		gallerydb.add_method_queue(gallerydb.ListDB.modify_list, True, self.gallery_list, True, True)
		gallerydb.add_method_queue(self.gallery_list.scan, True)
		self.close()

class GalleryListContextMenu(QMenu):
	def __init__(self, item, parent):
		super().__init__(parent)
		self.parent_widget = parent
		self.item = item
		self.gallery_list = item.item
		edit = self.addAction("Edit", self.edit_list)
		clear = self.addAction("Clear", self.clear_list)
		remove = self.addAction("Delete", self.remove_list)

	def edit_list(self):
		l_edit = GalleryListEdit(self.gallery_list, self.item, self.parent_widget)
		l_edit.show()

	def remove_list(self):
		self.parent_widget.takeItem(self.parent_widget.row(self.item))
		gallerydb.add_method_queue(gallerydb.ListDB.remove_list, True, self.gallery_list)
		self.parent_widget.GALLERY_LIST_REMOVED.emit()

	def clear_list(self):
		self.gallery_list.clear()
		self.parent_widget.GALLERY_LIST_CLICKED.emit(self.gallery_list)

class GalleryLists(QListWidget):
	CREATE_LIST_TYPE = misc.CustomListItem.UserType+1
	GALLERY_LIST_CLICKED = pyqtSignal(gallerydb.GalleryList)
	GALLERY_LIST_REMOVED = pyqtSignal()
	def __init__(self, parent):
		super().__init__(parent)
		self.setContentsMargins(0,0,0,0)
		self.setSpacing(0)
		add_item = misc.CustomListItem(txt="Create new list...", parent=self, type=self.CREATE_LIST_TYPE)
		add_item.setForeground(QBrush(QColor("gray")))
		self._font_selected = QFont(self.font())
		self._font_selected.setBold(True)
		self._font_selected.setUnderline(True)
		self._font = QFont(self.font())
		self._font.setItalic(True)
		self._font.setUnderline(True)
		add_item.setFont(self._font)
		add_item.setTextAlignment(Qt.AlignCenter)
		add_item.setFlags(Qt.ItemIsEnabled)
		add_item.setToolTip("Double click to create new list")
		self.itemDoubleClicked.connect(self._item_double_clicked)
		self.setItemDelegate(ListDelegate(self))
		self.itemDelegate().closeEditor.connect(self._add_new_list)
		self.setEditTriggers(self.NoEditTriggers)
		self._in_proccess_item = None
		self.current_selected = None

	def _add_new_list(self, lineedit=None, hint=None, gallery_list=None):
		if not self._in_proccess_item.text():
			self.takeItem(self.row(self._in_proccess_item))
			return
		new_item = self._in_proccess_item
		if not gallery_list:
			new_list = gallerydb.GalleryList(new_item.text())
			new_list.add_to_db()
		else:
			new_list = gallery_list
		new_item.item = new_list

	def create_new_list(self, name=None, gallery_list=None):
		new_item = misc.CustomListItem()
		self._in_proccess_item = new_item
		new_item.setFlags(new_item.flags() | Qt.ItemIsEditable)
		new_item.setIcon(QIcon(app_constants.LIST_PATH))
		self.insertItem(1, new_item)
		if name:
			new_item.setText(name)
			self._add_new_list(gallery_list=gallery_list)
		else:
			self.editItem(new_item)

	def _item_double_clicked(self, item):
		if item:
			if item.type() == self.CREATE_LIST_TYPE:
				self.create_new_list()
			else:
				if self.current_selected:
					self.current_selected.setFont(self.font())
				if item.item.filter:
					gallerydb.add_method_queue(item.item.scan, True)
				self.GALLERY_LIST_CLICKED.emit(item.item)
				item.setFont(self._font_selected)
				self.current_selected = item

	def setup_lists(self):
		for g_l in app_constants.GALLERY_LISTS:
			self.create_new_list(g_l.name, g_l)

	def contextMenuEvent(self, event):
		item = self.itemAt(event.pos())
		if item and item.type() != self.CREATE_LIST_TYPE:
			menu = GalleryListContextMenu(item, self)
			menu.exec_(event.globalPos())
			event.accept()
			return
		event.ignore()

class SideBarWidget(QFrame):
	"""
	"""
	def __init__(self, parent):
		super().__init__(parent)
		self.parent_widget = parent
		self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
		widget_layout = QHBoxLayout(self)

		# widget stuff
		self._d_widget = QWidget(self)
		widget_layout.addWidget(self._d_widget)
		self.main_layout = QVBoxLayout(self._d_widget)
		self.main_layout.setSpacing(0)
		self.main_layout.setContentsMargins(0,0,0,0)
		self.arrow_handle = misc.ArrowHandle(self)
		self.arrow_handle.CLICKED.connect(self.slide)

		widget_layout.addWidget(self.arrow_handle)
		self.setContentsMargins(0,0,-self.arrow_handle.width(),0)

		self.show_all_galleries_btn = QPushButton("Show all galleries")
		self.show_all_galleries_btn.clicked.connect(lambda:parent.manga_list_view.sort_model.set_gallery_list())
		self.show_all_galleries_btn.clicked.connect(self.show_all_galleries_btn.hide)
		self.show_all_galleries_btn.hide()
		self.main_layout.addWidget(self.show_all_galleries_btn)
		self.main_buttons_layout = QHBoxLayout()
		self.main_layout.addLayout(self.main_buttons_layout)

		# buttons
		self.lists_btn = QPushButton("Lists")
		self.artist_btn = QPushButton("Artists")
		self.ns_tags_btn = QPushButton("NS && Tags")
		self.main_buttons_layout.addWidget(self.lists_btn)
		self.main_buttons_layout.addWidget(self.artist_btn)
		self.main_buttons_layout.addWidget(self.ns_tags_btn)

		# buttons contents
		self.stacked_layout = QStackedLayout()
		self.main_layout.addLayout(self.stacked_layout)

		# lists
		self.lists = GalleryLists(self)
		lists_index = self.stacked_layout.addWidget(self.lists)
		self.lists.GALLERY_LIST_CLICKED.connect(parent.manga_list_view.sort_model.set_gallery_list)
		self.lists.GALLERY_LIST_CLICKED.connect(self.show_all_galleries_btn.show)
		self.lists.GALLERY_LIST_REMOVED.connect(self.show_all_galleries_btn.click)
		self.lists_btn.clicked.connect(lambda:self.stacked_layout.setCurrentIndex(lists_index))
		self.show_all_galleries_btn.clicked.connect(self.lists.clearSelection)

		# artists
		self.artists_list = GalleryArtistsList(parent.manga_list_view.gallery_model, self)
		self.artists_list.artist_clicked.connect(lambda a: parent.search('artist:"{}"'.format(a)))
		artists_list_index = self.stacked_layout.addWidget(self.artists_list)
		self.artist_btn.clicked.connect(lambda:self.stacked_layout.setCurrentIndex(artists_list_index))
		self.show_all_galleries_btn.clicked.connect(self.artists_list.clearSelection)

		# ns_tags
		self.tags_tree = TagsTreeView(self)
		self.tags_tree.TAG_SEARCH.connect(parent.search)
		self.tags_tree.NEW_LIST.connect(self.lists.create_new_list)
		self.tags_tree.setHeaderHidden(True)
		self.show_all_galleries_btn.clicked.connect(self.tags_tree.clearSelection)
		self.tags_layout = QVBoxLayout(self.tags_tree)
		ns_tags_index = self.stacked_layout.addWidget(self.tags_tree)
		self.ns_tags_btn.clicked.connect(lambda:self.stacked_layout.setCurrentIndex(ns_tags_index))
		if parent.manga_list_view.gallery_model.db_emitter._finished:
			self.tags_tree.setup_tags()
			self.lists.setup_lists()
		else:
			parent.manga_list_view.gallery_model.db_emitter.DONE.connect(self.tags_tree.setup_tags)
			parent.manga_list_view.gallery_model.db_emitter.DONE.connect(self.lists.setup_lists)

		self.adjustSize()
		self.slide_animation = misc.create_animation(self, "maximumSize")
		self.slide_animation.stateChanged.connect(self._slide_hide)
		self.slide_animation.setEasingCurve(QEasingCurve.InOutQuad)
		self._max_width = 300

	def _slide_hide(self, state):
		if state == self.slide_animation.Stopped:
			if self.arrow_handle.current_arrow == self.arrow_handle.OUT:
				self._d_widget.hide()
		elif self.slide_animation.Running:
			if self.arrow_handle.current_arrow == self.arrow_handle.IN:
				self._d_widget.show()

	def slide(self, state):
		self.slide_animation.setEndValue(QSize(self.arrow_handle.width()*2, self.height()))

		if state:
			self.slide_animation.setDirection(self.slide_animation.Forward)
			self.slide_animation.start()
		else:
			self.slide_animation.setDirection(self.slide_animation.Backward)
			self.slide_animation.start()

	def resizeEvent(self, event):
		self._max_width = self.parent_widget.width()*0.2
		self.setMaximumWidth(self._max_width)
		self.slide_animation.setStartValue(QSize(self._max_width, event.size().height()))
		return super().resizeEvent(event)


class DBOverview(QWidget):
	"""
	
	"""
	about_to_close = pyqtSignal()
	def __init__(self, parent, window=False):
		if window:
			super().__init__(None, Qt.Window)
		else:
			super().__init__(parent)
		self.setAttribute(Qt.WA_DeleteOnClose)
		self.parent_widget = parent
		main_layout = QVBoxLayout(self)
		tabbar = QTabWidget(self)
		main_layout.addWidget(tabbar)
		
		# Tags stats
		self.tags_stats = QListWidget(self)
		tabbar.addTab(self.tags_stats, 'Statistics')
		tabbar.setTabEnabled(1, False)

		# About AD
		self.about_db = QWidget(self)
		tabbar.addTab(self.about_db, 'DB Info')
		tabbar.setTabEnabled(2, False)

		self.resize(300, 600)
		self.setWindowTitle('DB Overview')
		self.setWindowIcon(QIcon(app_constants.APP_ICO_PATH))

	def setup_stats(self):
		pass

	def setup_about_db(self):
		pass

	def closeEvent(self, event):
		self.about_to_close.emit()
		return super().closeEvent(event)