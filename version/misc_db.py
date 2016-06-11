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
import pickle
import logging

from PyQt5.QtWidgets import (QTreeWidget, QTreeWidgetItem, QWidget,
                             QVBoxLayout, QTabWidget, QAction, QGraphicsScene,
                             QSizePolicy, QMenu, QAction, QApplication,
                             QListWidget, QHBoxLayout, QPushButton, QStackedLayout,
                             QFrame, QSizePolicy, QListView, QFormLayout, QLineEdit,
                             QLabel, QStyledItemDelegate, QStyleOptionViewItem,
                             QCheckBox, QButtonGroup, QSpacerItem)
from PyQt5.QtCore import (Qt, QTimer, pyqtSignal, QRect, QSize, QEasingCurve,
                          QSortFilterProxyModel, QIdentityProxyModel, QModelIndex,
                          QPointF, QRectF, QObject)
from PyQt5.QtGui import (QIcon, QStandardItem, QFont, QPainter, QColor, QBrush,
                         QPixmap, QPalette)

import gallerydb
import app_constants
import utils
import misc
import gallery

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical

class TabButton(QPushButton):
    close_tab = pyqtSignal(object)

    def __init__(self, txt, parent=None):
        super().__init__(txt, parent)

class TabManager(QObject):
    ""
    def __init__(self, sidebar, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.sidebar = sidebar
        self._last_selected = None

        self.agroup = QButtonGroup(self)
        self.agroup.setExclusive(True)

        self.sidebar.main_layout.insertSpacing(0, 50)
        self.sidebar.main_layout.insertSpacing(0, 5)

        self.library_btn = QPushButton(app_constants.GRID_ICON, "Library")
        self.library_btn.view = self.parent_widget.default_manga_view
        self.library_btn.setStyleSheet("text-align:left")
        self.library_btn.setCheckable(True)
        self.agroup.addButton(self.library_btn)
        self.sidebar.main_layout.insertWidget(0, self.library_btn)
        self.sidebar.main_layout.insertSpacing(0, 5)

        self.favorite_btn = QPushButton(app_constants.STAR_ICON, "Favorites")
        self.favorite_btn.setStyleSheet("text-align:left")
        self.favorite_btn.setCheckable(True)
        self.agroup.addButton(self.favorite_btn)
        self.sidebar.main_layout.insertWidget(0, self.favorite_btn)

        def switch_view(fav):
            if fav:
                self.default_manga_view.get_current_view().sort_model.fav_view()
            else:
                self.default_manga_view.get_current_view().sort_model.catalog_view()
        #self.favorite_btn.clicked.connect(lambda: switch_view(True))
        #self.library_btn.click()
        #self.library_btn.clicked.connect(lambda: switch_view(False))

    def _manage_selected(self, b):
        return
        if self._last_selected == b:
            return
        if self._last_selected:
            self._last_selected.selected = False
            self._last_selected.view.list_view.sort_model.rowsInserted.disconnect(self.parent_widget.stat_row_info)
            self._last_selected.view.list_view.sort_model.rowsRemoved.disconnect(self.parent_widget.stat_row_info)
            self._last_selected.view.hide()
        b.selected = True
        self._last_selected = b
        self.parent_widget.current_manga_view = b.view
        b.view.list_view.sort_model.rowsInserted.connect(self.parent_widget.stat_row_info)
        b.view.list_view.sort_model.rowsRemoved.connect(self.parent_widget.stat_row_info)
        b.view.show()

    def addTab(self, name, view_type=app_constants.ViewType.Default, delegate_paint=True, allow_sidebarwidget=False, icon=None, left_align=False):
        if self.sidebar:
            t = TabButton(name)
            t.setCheckable(True)
            if icon:
                t.setIcon(icon)
            if left_align:
                t.setStyleSheet("text-align:left")
            self.agroup.addButton(t)
            t.clicked.connect(self._manage_selected)
            t.close_tab.connect(self.removeTab)
            t.view = gallery.ViewManager(view_type, self.parent_widget, allow_sidebarwidget)
            t.view.hide()
            t.close_tab.connect(lambda:self.library_btn.click())
                #if not allow_sidebarwidget:
                #    t.clicked.connect(self.parent_widget.sidebar_list.arrow_handle.click)
            #if delegate_paint:
            #    t.view.list_view.grid_delegate._paint_level = 9000 # over nine thousand!!!
            self.sidebar.main_layout.insertWidget(4, t)
            return t

    def removeTab(self, button_or_index):
        if self.sidebar:
            if isinstance(button_or_index, int):
                self.sidebar.removeAction(self._actions.pop(button_or_index))
            else:
                act_to_remove = None
                for act in self._actions:
                    w = self.sidebar.widgetForAction(act)
                    if w == button_or_index:
                        self.sidebar.removeAction(act)
                        act_to_remove = act
                        break
                if act_to_remove:
                    self._actions.remove(act)

class NoTooltipModel(QIdentityProxyModel):

    def __init__(self, model, parent=None):
        super().__init__(parent)
        self.setSourceModel(model)

    def data(self, index, role=Qt.DisplayRole):
        if role == Qt.ToolTipRole:
            return None
        if role == Qt.DecorationRole:
            return QPixmap(app_constants.GARTIST_PATH)
        return self.sourceModel().data(index, role)



class UniqueInfoModel(QSortFilterProxyModel):
    def __init__(self, gallerymodel, role, parent=None):
        super().__init__(parent)
        self.setSourceModel(NoTooltipModel(gallerymodel, parent))
        self._unique = set()
        self._unique_role = role
        self.custom_filter = None
        self.setDynamicSortFilter(True)

    def filterAcceptsRow(self, source_row, parent_index):
        if self.sourceModel():
            idx = self.sourceModel().index(source_row, 0, parent_index)
            if idx.isValid():
                unique = idx.data(self._unique_role)
                if unique:
                    if not unique in self._unique:
                        if self.custom_filter != None:
                            if not idx.data(Qt.UserRole + 1) in self.custom_filter:
                                return False
                        self._unique.add(unique)
                        return True
        return False

    def invalidate(self):
        self._unique.clear()
        super().invalidate()

class ListDelegate(QStyledItemDelegate):
    def __init__(self, parent=None):
        self.parent_widget = parent
        super().__init__(parent)
        self.create_new_list_txt = 'Create new list...'
    
    def sizeHint(self, option, index):
        size = super().sizeHint(option, index)
        if index.data(Qt.DisplayRole) == self.create_new_list_txt:
            return size
        return QSize(size.width(), size.height() * 2)

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

    def _artist_clicked(self, idx):
        if idx.isValid():
            self.artist_clicked.emit(idx.data(self.ARTIST_ROLE))

    def set_current_glist(self, g_list=None):
        if g_list:
            self.g_artists_model.custom_filter = g_list
        else:
            self.g_artists_model.custom_filter = None
        self.g_artists_model.invalidate()

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
        contains_ns = True if ns_count > 0 else False

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
        tags = gallerydb.execute(gallerydb.TagDB.get_ns_tags, False)
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
    apply = pyqtSignal()
    def __init__(self, parent):
        super().__init__(parent, blur=False)
        main_layout = QFormLayout(self.main_widget)
        self.name_edit = QLineEdit(self)
        main_layout.addRow("Name:", self.name_edit)
        self.filter_edit = QLineEdit(self)
        what_is_filter = misc.ClickedLabel("What is filter/enforce? (Hover)")
        what_is_filter.setToolTip(app_constants.WHAT_IS_FILTER)
        what_is_filter.setToolTipDuration(9999999999)
        self.enforce = QCheckBox(self)
        self.regex = QCheckBox(self)
        self.case = QCheckBox(self)
        self.strict = QCheckBox(self)
        main_layout.addRow(what_is_filter)
        main_layout.addRow("Filter", self.filter_edit)
        main_layout.addRow("Enforce", self.enforce)
        main_layout.addRow("Regex", self.regex)
        main_layout.addRow("Case sensitive", self.case)
        main_layout.addRow("Match whole terms", self.strict)
        main_layout.addRow(self.buttons_layout)
        self.add_buttons("Close")[0].clicked.connect(self.hide)
        self.add_buttons("Apply")[0].clicked.connect(self.accept)

    def set_list(self, gallery_list, item):
        self.gallery_list = gallery_list
        self.name_edit.setText(gallery_list.name)
        self.enforce.setChecked(gallery_list.enforce)
        self.regex.setChecked(gallery_list.regex)
        self.case.setChecked(gallery_list.case)
        self.strict.setChecked(gallery_list.strict)
        self.item = item
        if gallery_list.filter:
            self.filter_edit.setText(gallery_list.filter)
        else:
            self.filter_edit.setText('')
        self.adjustSize()
        self.setFixedWidth(self.parent_widget.width())

    def accept(self):
        name = self.name_edit.text()
        self.item.setText(name)
        self.gallery_list.name = name
        self.gallery_list.filter = self.filter_edit.text()
        self.gallery_list.enforce = self.enforce.isChecked()
        self.gallery_list.regex = self.regex.isChecked()
        self.gallery_list.case = self.case.isChecked()
        self.gallery_list.strict = self.strict.isChecked()
        gallerydb.execute(gallerydb.ListDB.modify_list, True, self.gallery_list)
        self.apply.emit()
        self.hide()

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
        self.parent_widget.gallery_list_edit.set_list(self.gallery_list, self.item)
        self.parent_widget.gallery_list_edit.show()

    def remove_list(self):
        self.parent_widget.takeItem(self.parent_widget.row(self.item))
        gallerydb.execute(gallerydb.ListDB.remove_list, True, self.gallery_list)
        self.parent_widget.GALLERY_LIST_REMOVED.emit()

    def clear_list(self):
        self.gallery_list.clear()
        self.parent_widget.GALLERY_LIST_CLICKED.emit(self.gallery_list)

class GalleryLists(QListWidget):
    CREATE_LIST_TYPE = misc.CustomListItem.UserType + 1
    GALLERY_LIST_CLICKED = pyqtSignal(gallerydb.GalleryList)
    GALLERY_LIST_REMOVED = pyqtSignal()
    def __init__(self, parent):
        super().__init__(parent)
        self.gallery_list_edit = GalleryListEdit(parent)
        self.gallery_list_edit.hide()
        self._g_list_icon = QIcon(app_constants.GLIST_PATH)
        self._font_selected = QFont(self.font())
        self._font_selected.setBold(True)
        self._font_selected.setUnderline(True)
        self.itemDoubleClicked.connect(self._item_double_clicked)
        self.setItemDelegate(ListDelegate(self))
        self.itemDelegate().closeEditor.connect(self._add_new_list)
        self.setEditTriggers(self.NoEditTriggers)
        self.viewport().setAcceptDrops(True)
        self._in_proccess_item = None
        self.current_selected = None
        self.gallery_list_edit.apply.connect(lambda: self._item_double_clicked(self.current_selected))
        self.setup_lists()

    def dragEnterEvent(self, event):
        if event.mimeData().hasFormat("list/gallery"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        item = self.itemAt(event.pos())
        self.clearSelection()
        if item:
            item.setSelected(True)
        event.accept()

    def dropEvent(self, event):
        galleries = []

        galleries = pickle.loads(event.mimeData().data("list/gallery").data())

        g_list_item = self.itemAt(event.pos())
        if galleries and g_list_item:
            txt = "galleries" if len(galleries) > 1 else "gallery"
            app_constants.NOTIF_BUBBLE.update_text(g_list_item.item.name, 'Added {} to list...'.format(txt), 5)
            log_i('Adding gallery to list')
            g_list_item.item.add_gallery(galleries)

        super().dropEvent(event)


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
        new_item.setIcon(self._g_list_icon)
        self.sortItems()

    def create_new_list(self, name=None, gallery_list=None):
        new_item = misc.CustomListItem()
        self._in_proccess_item = new_item
        new_item.setFlags(new_item.flags() | Qt.ItemIsEditable)
        new_item.setIcon(QIcon(app_constants.LIST_PATH))
        self.insertItem(0, new_item)
        if name:
            new_item.setText(name)
            self._add_new_list(gallery_list=gallery_list)
        else:
            self.editItem(new_item)

    def _item_double_clicked(self, item):
        if item:
            self._reset_selected()
            if item.item.filter:
                app_constants.NOTIF_BUBBLE.update_text(item.item.name, "Updating list..", 5)
                gallerydb.execute(item.item.scan, True)
            self.GALLERY_LIST_CLICKED.emit(item.item)
            item.setFont(self._font_selected)
            self.current_selected = item

    def _reset_selected(self):
        if self.current_selected:
            self.current_selected.setFont(self.font())

    def setup_lists(self):
        for g_l in app_constants.GALLERY_LISTS:
            if g_l.type == gallerydb.GalleryList.REGULAR:
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
        self.setAcceptDrops(True)
        self.setFixedWidth(200)
        self.parent_widget = parent
        self.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Expanding)
        self.parent_widget
        self._widget_layout = QHBoxLayout(self)

        # widget stuff
        self._d_widget = QWidget(self)
        self._widget_layout.addWidget(self._d_widget)
        self.main_layout = QVBoxLayout(self._d_widget)
        self.main_layout.setSpacing(0)
        self.main_layout.setContentsMargins(0,0,0,0)
        #self.arrow_handle = misc.ArrowHandle(self)
        #self.arrow_handle.CLICKED.connect(self.slide)

        #self._widget_layout.addWidget(self.arrow_handle)
        #self.setContentsMargins(0,0,-self.arrow_handle.width(),0)

        self.show_all_galleries_btn = QPushButton("Show all galleries")
        self.show_all_galleries_btn.clicked.connect(lambda:parent.manga_list_view.sort_model.set_gallery_list())
        self.show_all_galleries_btn.clicked.connect(self.show_all_galleries_btn.hide)
        self.show_all_galleries_btn.hide()
        self.main_layout.addWidget(self.show_all_galleries_btn)
        self.main_buttons_layout = QHBoxLayout()
        self.main_layout.addLayout(self.main_buttons_layout)

        # buttons
        bgroup = QButtonGroup(self)
        bgroup.setExclusive(True)
        self.lists_btn = QPushButton(app_constants.G_LISTS_ICON, "")
        self.lists_btn.setCheckable(True)
        bgroup.addButton(self.lists_btn)
        self.artist_btn = QPushButton(app_constants.ARTISTS_ICON, "")
        self.artist_btn.setCheckable(True)
        bgroup.addButton(self.artist_btn)
        self.ns_tags_btn = QPushButton(app_constants.NSTAGS_ICON, "")
        self.ns_tags_btn.setCheckable(True)
        bgroup.addButton(self.ns_tags_btn)
        self.lists_btn.setChecked(True)


        self.main_buttons_layout.addWidget(self.lists_btn)
        self.main_buttons_layout.addWidget(self.artist_btn)
        self.main_buttons_layout.addWidget(self.ns_tags_btn)

        # buttons contents
        self.stacked_layout = QStackedLayout()
        self.main_layout.addLayout(self.stacked_layout)

        # lists
        gallery_lists_dummy = QWidget(self)
        self.lists = GalleryLists(self)
        create_new_list_btn = QPushButton()
        create_new_list_btn.setIcon(app_constants.PLUS_ICON)
        create_new_list_btn.setIconSize(QSize(15, 15))
        create_new_list_btn.clicked.connect(lambda: self.lists.create_new_list())
        create_new_list_btn.adjustSize()
        create_new_list_btn.setFixedSize(create_new_list_btn.width(), create_new_list_btn.height())
        create_new_list_btn.setToolTip("Create a new list!")
        lists_l = QVBoxLayout(gallery_lists_dummy)
        lists_l.setContentsMargins(0,0,0,0)
        lists_l.setSpacing(0)
        lists_l.addWidget(self.lists)
        lists_l.addWidget(create_new_list_btn)
        lists_index = self.stacked_layout.addWidget(gallery_lists_dummy)
        self.lists.GALLERY_LIST_CLICKED.connect(parent.manga_list_view.sort_model.set_gallery_list)
        self.lists.GALLERY_LIST_CLICKED.connect(self.show_all_galleries_btn.show)
        self.lists.GALLERY_LIST_REMOVED.connect(self.show_all_galleries_btn.click)
        self.lists_btn.clicked.connect(lambda:self.stacked_layout.setCurrentIndex(lists_index))
        self.show_all_galleries_btn.clicked.connect(self.lists.clearSelection)
        self.show_all_galleries_btn.clicked.connect(self.lists._reset_selected)

        ## artists
        #self.artists_list = GalleryArtistsList(parent.manga_list_view.gallery_model, self)
        #self.artists_list.artist_clicked.connect(lambda a: parent.search('artist:"{}"'.format(a)))
        #artists_list_index = self.stacked_layout.addWidget(self.artists_list)
        #self.artist_btn.clicked.connect(lambda:self.stacked_layout.setCurrentIndex(artists_list_index))
        ##self.lists.GALLERY_LIST_CLICKED.connect(self.artists_list.set_current_glist)
        #self.show_all_galleries_btn.clicked.connect(self.artists_list.clearSelection)
        ##self.show_all_galleries_btn.clicked.connect(lambda:self.artists_list.set_current_glist())

        # ns_tags
        self.tags_tree = TagsTreeView(self)
        self.tags_tree.TAG_SEARCH.connect(parent.search)
        self.tags_tree.NEW_LIST.connect(self.lists.create_new_list)
        self.tags_tree.setHeaderHidden(True)
        self.show_all_galleries_btn.clicked.connect(self.tags_tree.clearSelection)
        self.tags_layout = QVBoxLayout(self.tags_tree)
        ns_tags_index = self.stacked_layout.addWidget(self.tags_tree)
        self.ns_tags_btn.clicked.connect(lambda:self.stacked_layout.setCurrentIndex(ns_tags_index))

    #    self.slide_animation = misc.create_animation(self, "maximumSize")
    #    self.slide_animation.stateChanged.connect(self._slide_hide)
    #    self.slide_animation.setEasingCurve(QEasingCurve.InOutQuad)

    #def _slide_hide(self, state):
    #    size = self.sizeHint()
    #    if state == self.slide_animation.Stopped:
    #        if self.arrow_handle.current_arrow == self.arrow_handle.OUT:
    #            self._d_widget.hide()
    #    elif self.slide_animation.Running:
    #        if self.arrow_handle.current_arrow == self.arrow_handle.IN:
    #            if not self.parent_widget.current_manga_view.allow_sidebarwidget:
    #                self.arrow_handle.current_arrow = self.arrow_handle.OUT
    #                self.arrow_handle.update()
    #            else:
    #                self._d_widget.show()


    #def slide(self, state):
    #    self.slide_animation.setEndValue(QSize(self.arrow_handle.width() * 2, self.height()))

    #    if state:
    #        self.slide_animation.setDirection(self.slide_animation.Forward)
    #        self.slide_animation.start()
    #    else:
    #        self.slide_animation.setDirection(self.slide_animation.Backward)
    #        self.slide_animation.start()

    def showEvent(self, event):
        super().showEvent(event)
        #if not app_constants.SHOW_SIDEBAR_WIDGET:
        #    self.arrow_handle.click()

    #def _init_size(self, event=None):
    #    h = self.parent_widget.height()
    #    self._max_width = 200
    #    self.updateGeometry()
    #    self.setMaximumWidth(self._max_width)
    #    self.slide_animation.setStartValue(QSize(self._max_width, h))

    def resizeEvent(self, event):
        #self._init_size(event)
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