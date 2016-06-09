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

import threading
import logging
import os
import math
import functools
import random
import datetime
import pickle
import enum
import time
import re as regex

from PyQt5.QtCore import (Qt, QAbstractListModel, QModelIndex, QVariant,
                          QSize, QRect, QEvent, pyqtSignal, QThread,
                          QTimer, QPointF, QSortFilterProxyModel,
                          QAbstractTableModel, QItemSelectionModel,
                          QPoint, QRectF, QDate, QDateTime, QObject,
                          QEvent, QSizeF, QMimeData, QByteArray, QTime)
from PyQt5.QtGui import (QPixmap, QBrush, QColor, QPainter, 
                         QPen, QTextDocument,
                         QMouseEvent, QHelpEvent,
                         QPixmapCache, QCursor, QPalette, QKeyEvent,
                         QFont, QTextOption, QFontMetrics, QFontMetricsF,
                         QTextLayout, QPainterPath, QScrollPrepareEvent,
                         QWheelEvent, QPolygonF, QLinearGradient, QStandardItemModel,
                         QStandardItem)
from PyQt5.QtWidgets import (QListView, QFrame, QLabel,
                             QStyledItemDelegate, QStyle,
                             QMenu, QAction, QToolTip, QVBoxLayout,
                             QSizePolicy, QTableWidget, QScrollArea,
                             QHBoxLayout, QFormLayout, QDesktopWidget,
                             QWidget, QHeaderView, QTableView, QApplication,
                             QMessageBox, QActionGroup, QScroller, QStackedLayout,
                             QTreeView, QPushButton)

import gallerydb
import app_constants
import db_constants
import misc
import gallerydialog
import io_misc
import utils
import db

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical

# attempt at implementing treemodel

class BaseItem(QStandardItem):

    def __init__(self):
        super().__init__()
        self._delegate = {}

    def data(self, role = Qt.UserRole+1):

        if role == app_constants.DELEGATE_ROLE:
            return self._delegate
        elif role == app_constants.QITEM_ROLE:
            return self

        return super().data(role)

    def setData(self, value, role = Qt.UserRole+1):

        if role == app_constants.DELEGATE_ROLE:
            self._delegate[value[0]] = value[1]

        return super().setData(value, role)

class CollectionItem(BaseItem):

    def __init__(self, collection):
        assert isinstance(collection, db.Collection)
        super().__init__()
        self._item = collection

    def data(self, role = Qt.UserRole+1):

        if role in (Qt.DisplayRole, app_constants.TITLE_ROLE):
            return self._item.title
        elif role == Qt.DecorationRole:
            return QPixmap(self._item.profile)
        elif role == app_constants.ITEM_ROLE:
            return self._item
        elif role == app_constants.INFO_ROLE:
            return self._item.info

        return super().data(role)

    def setData(self, value, role = Qt.UserRole+1):

        if role == Qt.DisplayRole:
            self._item.title = value
        elif role == app_constants.TITLE_ROLE:
            self._item.title = value
        elif role == app_constants.INFO_ROLE:
            self._item.info = value

        return super().setData(value, role)

    @classmethod
    def type(self):
        return self.UserType+1

class GalleryItem(BaseItem):

    def __init__(self, gallery):
        assert isinstance(gallery, db.Gallery)
        super().__init__()
        self._item = gallery

    def data(self, role = Qt.UserRole+1):

        if role in (Qt.DisplayRole, app_constants.TITLE_ROLE):
            return self._item.title
        elif role == Qt.DecorationRole:
            return QImage(self._item.profile)
        elif role == app_constants.ITEM_ROLE:
            return self._item
        elif role == app_constants.ARTIST_ROLE:
            print(self._item.artists)
            if not self._item.artists:
                return []
            return self._item.artists
        elif role == app_constants.FAV_ROLE:
            return self._item.fav
        elif role == app_constants.INFO_ROLE:
            return self._item.info
        elif role == app_constants.TYPE_ROLE:
            return self._item.type
        elif role == app_constants.LANGUAGE_ROLE:
            return self._item.language
        elif role == app_constants.RATING_ROLE:
            return self._item.rating
        elif role == app_constants.TIMES_READ_ROLE:
            return self._item.times_read
        elif role == app_constants.STATUS_ROLE:
            return self._item.status
        elif role == app_constants.PUB_DATE_ROLE:
            return self._item.pub_date
        elif role == app_constants.DATE_ADDED_ROLE:
            return self._item.timestamp
        elif role == app_constants.NUMBER_ROLE:
            return self._item.number
        elif role == app_constants.CONVENTION_ROLE:
            return self._item.convention
        elif role == app_constants.PARENT_ROLE:
            return self._item.parent
        elif role == app_constants.COLLECTION_ROLE:
            return self._item.collection
        elif role == app_constants.TAGS_ROLE:
            return self._item.tags
        elif role == app_constants.CIRCLES_ROLE:
            return self._item.circles
        elif role == app_constants.URLS_ROLE:
            return self._item.urls

        return super().data(role)

    def setData(self, value, role = Qt.UserRole+1):

        if role == Qt.DisplayRole:
            self._item.title = value
        elif role == app_constants.TITLE_ROLE:
            self._item.title = value
        elif role == app_constants.INFO_ROLE:
            self._item.info = value

        return super().setData(value, role)

    @classmethod
    def type(self):
        return self.UserType+2

class PageItem(BaseItem):

    def __init__(self, page):
        assert isinstance(page, db.Page)
        super().__init__()
        self._item = page

    def data(self, role = Qt.UserRole+1):

        if role in (Qt.DisplayRole, app_constants.TITLE_ROLE):
            pname = "Page"
            if self._item.number:
                pname += " " + str(self._item.number)
            return pname
        elif role == Qt.DecorationRole:
            return QPixmap(self._item.profile)
        elif role == app_constants.ITEM_ROLE:
            return self._item
        elif role == app_constants.NUMBER_ROLE:
            return self._item.number
        elif role == app_constants.PARENT_ROLE:
            return self._item.gallery
        elif role == app_constants.HASH_ROLE:
            _hash = None
            if self._item.hash:
                _hash = self._item.hash.name
            return _hash

        return super().data(role)

    def setData(self, value, role = Qt.UserRole+1):

        if role == Qt.DisplayRole:
            self._item.title = value
        elif role == app_constants.TITLE_ROLE:
            self._item.title = value

        return super().setData(value, role)

    @classmethod
    def type(self):
        return self.UserType+3


class GallerySearch(QObject):
    FINISHED = pyqtSignal()
    def __init__(self, data):
        super().__init__()
        self._data = data
        self.result = {}

        # filtering
        self.fav = False
        self._gallery_list = None

    def set_gallery_list(self, g_list):
        self._gallery_list = g_list

    def set_data(self, new_data):
        self._data = new_data
        self.result = {g.id: True for g in self._data}

    def set_fav(self, new_fav):
        self.fav = new_fav

    def search(self, term, args):
        term = ' '.join(term.split())
        search_pieces = utils.get_terms(term)

        self._filter(search_pieces, args)
        self.FINISHED.emit()

    def _filter(self, terms, args):
        self.result.clear()
        for gallery in self._data:
            if self.fav:
                if not gallery.fav:
                    continue
            if self._gallery_list:
                if not gallery in self._gallery_list:
                    continue
            all_terms = {t: False for t in terms}
            allow = False
            if utils.all_opposite(terms):
                self.result[gallery.id] = True
                continue
            
            for t in terms:
                if gallery.contains(t, args):
                    all_terms[t] = True

            if all(all_terms.values()):
                allow = True

            self.result[gallery.id] = allow

class SortFilterModel(QSortFilterProxyModel):
    ROWCOUNT_CHANGE = pyqtSignal()
    _DO_SEARCH = pyqtSignal(str, object)
    _CHANGE_SEARCH_DATA = pyqtSignal(list)
    _CHANGE_FAV = pyqtSignal(bool)
    _SET_GALLERY_LIST = pyqtSignal(object)

    HISTORY_SEARCH_TERM = pyqtSignal(str)
    # Navigate terms
    NEXT, PREV = range(2)
    # Views
    CAT_VIEW, FAV_VIEW = range(2)

    def __init__(self, parent):
        super().__init__(parent)
        self.parent_widget = parent
        self._data = app_constants.GALLERY_DATA
        self._search_ready = False
        self.current_term = ''
        self.terms_history = []
        self.current_term_history = 0
        self.current_gallery_list = None
        self.current_args = []
        self.current_view = self.CAT_VIEW
        self.setDynamicSortFilter(True)
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)
        self.setSortLocaleAware(True)
        self.setSortCaseSensitivity(Qt.CaseInsensitive)
        self.enable_drag = False

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
                self.init_search(new_term, history=False)
        return new_term

    def set_gallery_list(self, g_list=None):
        self.current_gallery_list = g_list
        self._SET_GALLERY_LIST.emit(g_list)
        self.refresh()

    def fav_view(self):
        self._CHANGE_FAV.emit(True)
        self.refresh()
        self.current_view = self.FAV_VIEW

    def catalog_view(self):
        self._CHANGE_FAV.emit(False)
        self.refresh()
        self.current_view = self.CAT_VIEW

    def setup_search(self):
        if not self._search_ready:
            self.gallery_search = GallerySearch(self.sourceModel()._data)
            self.gallery_search.FINISHED.connect(self.invalidateFilter)
            self.gallery_search.FINISHED.connect(lambda: self.ROWCOUNT_CHANGE.emit())
            self.gallery_search.moveToThread(app_constants.GENERAL_THREAD)
            self._DO_SEARCH.connect(self.gallery_search.search)
            self._SET_GALLERY_LIST.connect(self.gallery_search.set_gallery_list)
            self._CHANGE_SEARCH_DATA.connect(self.gallery_search.set_data)
            self._CHANGE_FAV.connect(self.gallery_search.set_fav)
            self.sourceModel().rowsInserted.connect(self.refresh)
            self._search_ready = True

    def refresh(self):
        self._DO_SEARCH.emit(self.current_term, self.current_args)

    def init_search(self, term, args=None, **kwargs):
        """
        Receives a search term and initiates a search
        args should be a list of Search enums
        """
        if not args:
            args = self.current_args
        history = kwargs.pop('history', True)
        if history:
            if len(self.terms_history) > 10:
                self.terms_history = self.terms_history[-10:]
            self.terms_history.append(term)

            self.current_term_history = len(self.terms_history) - 1
            if self.current_term_history < 0:
                self.current_term_history = 0

        self.current_term = term
        if not history:
            self.HISTORY_SEARCH_TERM.emit(term)
        self.current_args = args
        self._DO_SEARCH.emit(term, args)

    def filterAcceptsRow(self, source_row, parent_index):
        if self.sourceModel():
            index = self.sourceModel().index(source_row, 0, parent_index)
            if index.isValid():
                if self._search_ready:
                    gallery = index.data(Qt.UserRole + 1)
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
        self.refresh()

    def change_data(self, data):
        self._CHANGE_SEARCH_DATA.emit(data)

    def status_b_msg(self, msg):
        self.sourceModel().status_b_msg(msg)

    def canDropMimeData(self, data, action, row, coloumn, index):
        return False
        if not data.hasFormat("list/gallery"):
            return False
        return True

    def dropMimeData(self, data, action, row, coloumn, index):
        if not self.canDropMimeData(data, action, row, coloumn, index):
            return False
        if action == Qt.IgnoreAction:
            return True
        
        # if the drop occured on an item
        if not index.isValid():
            return False

        g_list = pickle.loads(data.data("list/gallery").data())
        item_g = index.data(GalleryModel.GALLERY_ROLE)
        # ignore false positive
        for g in g_list:
            if g.id == item_g.id:
                return False

        txt = 'galleries' if len(g_list) > 1 else 'gallery'
        msg = QMessageBox(self.parent_widget)
        msg.setText("Are you sure you want to merge the galleries into this gallery as chapter(s)?".format(txt))
        msg.setStandardButtons(msg.Yes | msg.No)
        if msg.exec() == msg.No:
            return False
        
        # TODO: finish this

        return True

    def mimeTypes(self):
        return ['list/gallery'] + super().mimeTypes()

    def mimeData(self, index_list):
        data = QMimeData()
        g_list = []
        for idx in index_list:
            g = idx.data(GalleryModel.GALLERY_ROLE)
            if g != None:
                g_list.append(g)
        data.setData("list/gallery", QByteArray(pickle.dumps(g_list)))
        return data

    def flags(self, index):
        default_flags = super().flags(index)
        
        if self.enable_drag:
            if (index.isValid()):
                return Qt.ItemIsDragEnabled | Qt.ItemIsDropEnabled | default_flags
            else:
                return Qt.ItemIsDropEnabled | default_flags
        return default_flags

    def supportedDragActions(self):
        return Qt.ActionMask

class StarRating():
    # enum EditMode
    Editable, ReadOnly = range(2)

    PaintingScaleFactor = 18

    def __init__(self, starCount=1, maxStarCount=5):
        self._starCount = starCount
        self._maxStarCount = maxStarCount

        self.starPolygon = QPolygonF([QPointF(1.0, 0.5)])
        for i in range(5):
            self.starPolygon << QPointF(0.5 + 0.5 * math.cos(0.8 * i * math.pi),
                                        0.5 + 0.5 * math.sin(0.8 * i * math.pi))

        self.diamondPolygon = QPolygonF()
        self.diamondPolygon << QPointF(0.4, 0.5) \
                            << QPointF(0.5, 0.4) \
                            << QPointF(0.6, 0.5) \
                            << QPointF(0.5, 0.6) \
                            << QPointF(0.4, 0.5)

    def starCount(self):
        return self._starCount

    def maxStarCount(self):
        return self._maxStarCount

    def setStarCount(self, starCount):
        self._starCount = starCount

    def setMaxStarCount(self, maxStarCount):
        self._maxStarCount = maxStarCount

    def sizeHint(self):
        return self.PaintingScaleFactor * QSize(self._maxStarCount, 1)

    def paint(self, painter, rect, editMode=ReadOnly):
        painter.save()

        painter.setRenderHint(QPainter.Antialiasing, True)
        painter.setPen(Qt.NoPen)

        painter.setBrush(QBrush(QColor(0, 0, 0, 100)))
        painter.drawRoundedRect(QRectF(rect), 2, 2)

        painter.setBrush(QBrush(Qt.yellow))

        scaleFactor = self.PaintingScaleFactor
        yOffset = (rect.height() - scaleFactor) / 2
        painter.translate(rect.x(), rect.y() + yOffset)
        painter.scale(scaleFactor, scaleFactor)

        for i in range(self._maxStarCount):
            if i < self._starCount:
                painter.drawPolygon(self.starPolygon, Qt.WindingFill)
            elif editMode == StarRating.Editable:
                painter.drawPolygon(self.diamondPolygon, Qt.WindingFill)

            painter.translate(1.0, 0.0)

        painter.restore()

class GalleryModel(QAbstractTableModel):
    """
    Model for Model/View/Delegate framework
    """
    GALLERY_ROLE = Qt.UserRole + 1
    ARTIST_ROLE = Qt.UserRole + 2
    FAV_ROLE = Qt.UserRole + 3
    DATE_ADDED_ROLE = Qt.UserRole + 4
    PUB_DATE_ROLE = Qt.UserRole + 5
    TIMES_READ_ROLE = Qt.UserRole + 6
    LAST_READ_ROLE = Qt.UserRole + 7
    TIME_ROLE = Qt.UserRole + 8
    RATING_ROLE = Qt.UserRole + 9

    ROWCOUNT_CHANGE = pyqtSignal()
    STATUSBAR_MSG = pyqtSignal(str)
    CUSTOM_STATUS_MSG = pyqtSignal(str)
    ADDED_ROWS = pyqtSignal()
    ADD_MORE = pyqtSignal()

    REMOVING_ROWS = False

    def __init__(self, data, parent=None):
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

        self._data = data
        self._data_count = 0 # number of items added to model
        self._gallery_to_add = []
        self._gallery_to_remove = []

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
        if role == self.ARTIST_ROLE:
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
                add_tips.append(utils.tag_to_string(current_gallery.tags))
            if app_constants.TOOLTIP_LAST_READ:
                add_bold.append('<b>Last read:</b>')
                add_tips.append('{} ago'.format(utils.get_date_age(current_gallery.last_read)) if current_gallery.last_read else "Never!")
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

        if role == self.GALLERY_ROLE:
            return current_gallery

        # favorite satus
        if role == self.FAV_ROLE:
            return current_gallery.fav

        if role == self.DATE_ADDED_ROLE:
            date_added = "{}".format(current_gallery.date_added)
            qdate_added = QDateTime.fromString(date_added, "yyyy-MM-dd HH:mm:ss")
            return qdate_added
        
        if role == self.PUB_DATE_ROLE:
            if current_gallery.pub_date:
                pub_date = "{}".format(current_gallery.pub_date)
                qpub_date = QDateTime.fromString(pub_date, "yyyy-MM-dd HH:mm:ss")
                return qpub_date

        if role == self.TIMES_READ_ROLE:
            return current_gallery.times_read

        if role == self.LAST_READ_ROLE:
            if current_gallery.last_read:
                last_read = "{}".format(current_gallery.last_read)
                qlast_read = QDateTime.fromString(last_read, "yyyy-MM-dd HH:mm:ss")
                return qlast_read

        if role == self.TIME_ROLE:
            return current_gallery.qtime

        if role == self.RATING_ROLE:
            return StarRating(current_gallery.rating)

        return None

    def rowCount(self, index=QModelIndex()):
        if index.isValid():
            return 0
        return len(self._data)

    def columnCount(self, parent=QModelIndex()):
        return len(app_constants.COLUMNS)

    def headerData(self, section, orientation, role=Qt.DisplayRole):
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


    def insertRows(self, position, rows, index=QModelIndex()):
        self._data_count += rows
        if not self._gallery_to_add:
            return False

        self.beginInsertRows(QModelIndex(), position, position + rows - 1)
        for r in range(rows):
            self._data.insert(position, self._gallery_to_add.pop())
        self.endInsertRows()
        return True

    def replaceRows(self, list_of_gallery, position, rows=1, index=QModelIndex()):
        "replaces gallery data to the data list WITHOUT adding to DB"
        for pos, gallery in enumerate(list_of_gallery):
            del self._data[position + pos]
            self._data.insert(position + pos, gallery)
        self.dataChanged.emit(index, index, [Qt.UserRole + 1, Qt.DecorationRole])

    def removeRows(self, position, rows, index=QModelIndex()):
        self._data_count -= rows
        self.beginRemoveRows(QModelIndex(), position, position + rows - 1)
        for r in range(rows):
            try:
                self._data.remove(self._gallery_to_remove.pop())
            except ValueError:
                return False
        self.endRemoveRows()
        return True

class GalleryDelegate(QStyledItemDelegate):
    "A custom delegate for the model/view framework"

    POPUP = pyqtSignal()
    CONTEXT_ON = False

    def __init__(self, app_inst, parent):
        super().__init__(parent)
        QPixmapCache.setCacheLimit(app_constants.THUMBNAIL_CACHE_SIZE[0] * app_constants.THUMBNAIL_CACHE_SIZE[1])
        self._painted_indexes = {}
        self.view = parent
        self.parent_widget = app_inst
        self._paint_level = 99

        self.font_size = app_constants.GALLERY_FONT[1]
        self.font_name = 0 # app_constants.GALLERY_FONT[0]
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
        self.H = app_constants.THUMB_H_SIZE + app_constants.GRIDBOX_LBL_H

    def key(self, key):
        "Assigns an unique key to indexes"
        if key in self._painted_indexes:
            return self._painted_indexes[key]
        else:
            k = str(key)
            self._painted_indexes[key] = k
            return k

    def _increment_paint_level(self):
        self._paint_level += 1
        self.view.update()

    def paint(self, painter, option, index):
        assert isinstance(painter, QPainter)
        rec = option.rect.getRect()
        x = rec[0]
        y = rec[1]
        w = rec[2]
        h = rec[3]
        if index.data(app_constants.QITEM_ROLE).type() == GalleryItem.type():
            if self._paint_level:
                #if app_constants.HIGH_QUALITY_THUMBS:
                #	painter.setRenderHint(QPainter.SmoothPixmapTransform)
                painter.setRenderHint(QPainter.Antialiasing)
                star_rating = StarRating(index.data(app_constants.RATING_ROLE))
                title = index.data(app_constants.TITLE_ROLE)
                artists = index.data(app_constants.ARTIST_ROLE)
                print(artists)
                artist = ""
                for n, a in enumerate(artists, 1):
                    artist += a.name
                    if n != artists.count():
                        artist += " & "

                title_color = app_constants.GRID_VIEW_TITLE_COLOR
                artist_color = app_constants.GRID_VIEW_ARTIST_COLOR
                label_color = app_constants.GRID_VIEW_LABEL_COLOR
                # Enable this to see the defining box
                #painter.drawRect(option.rect)
                # define font size
                if 20 > len(title) > 15:
                    title_size = "font-size:{}pt;".format(self.font_size)
                elif 30 > len(title) > 20:
                    title_size = "font-size:{}pt;".format(self.font_size - 1)
                elif 40 > len(title) >= 30:
                    title_size = "font-size:{}pt;".format(self.font_size - 2)
                elif 50 > len(title) >= 40:
                    title_size = "font-size:{}pt;".format(self.font_size - 3)
                elif len(title) >= 50:
                    title_size = "font-size:{}pt;".format(self.font_size - 4)
                else:
                    title_size = "font-size:{}pt;".format(self.font_size)

                if 30 > len(artist) > 20:
                    artist_size = "font-size:{}pt;".format(self.font_size)
                elif 40 > len(artist) >= 30:
                    artist_size = "font-size:{}pt;".format(self.font_size - 1)
                elif len(artist) >= 40:
                    artist_size = "font-size:{}pt;".format(self.font_size - 2)
                else:
                    artist_size = "font-size:{}pt;".format(self.font_size)

                text_area = QTextDocument()
                text_area.setDefaultFont(option.font)
                text_area.setHtml("""
                <head>
                <style>
                #area
                {{
                    display:flex;
                    width:{6}pt;
                    height:{7}pt;
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
                top:20pt;
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
                  130 + app_constants.SIZE_FACTOR, 1 + app_constants.SIZE_FACTOR))
                text_area.setTextWidth(w)

                def center_img(width):
                    new_x = x
                    if width < w:
                        diff = w - width
                        offset = diff // 2
                        new_x += offset
                    return new_x

                def img_too_big(start_x):
                    txt_layout = misc.text_layout("Thumbnail regeneration needed!", w, self.title_font, self.title_font_m)

                    clipping = QRectF(x, y + h // 4, w, app_constants.GRIDBOX_LBL_H - 10)
                    txt_layout.draw(painter, QPointF(x, y + h // 4),
                          clip=clipping)

                loaded_image = index.data(Qt.DecorationRole)
                if loaded_image and self._paint_level > 0 and self.view.scroll_speed < 600:
                    # if we can't find a cached image
                    pix_cache = QPixmapCache.find(self.key(loaded_image.cacheKey()))
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
                        self.image = QPixmap.fromImage(loaded_image)
                        img_x = center_img(self.image.width())
                        QPixmapCache.insert(self.key(loaded_image.cacheKey()), self.image)
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

                    painter.save()
                    painter.setPen(QColor(164,164,164,200))
                    if loaded_image:
                        thumb_text = "Loading..."
                    else:
                        thumb_text = "Thumbnail regeneration needed!"
                    txt_layout = misc.text_layout(thumb_text, w, self.title_font, self.title_font_m)

                    clipping = QRectF(x, y + h // 4, w, app_constants.GRIDBOX_LBL_H - 10)
                    txt_layout.draw(painter, QPointF(x, y + h // 4),
                          clip=clipping)
                    painter.restore()

                # draw ribbon type
                painter.save()
                painter.setPen(Qt.NoPen)
                if app_constants.DISPLAY_GALLERY_RIBBON:
                    type_ribbon_w = type_ribbon_l = w * 0.11
                    rib_top_1 = QPointF(x + w - type_ribbon_l - type_ribbon_w, y)
                    rib_top_2 = QPointF(x + w - type_ribbon_l, y)
                    rib_side_1 = QPointF(x + w, y + type_ribbon_l)
                    rib_side_2 = QPointF(x + w, y + type_ribbon_l + type_ribbon_w)
                    ribbon_polygon = QPolygonF([rib_top_1, rib_top_2, rib_side_1, rib_side_2])
                    ribbon_path = QPainterPath()
                    ribbon_path.setFillRule(Qt.WindingFill)
                    ribbon_path.addPolygon(ribbon_polygon)
                    ribbon_path.closeSubpath()
                    painter.setBrush(QBrush(QColor(self._ribbon_color(index.data(app_constants.TYPE_ROLE)))))
                    painter.drawPath(ribbon_path)

                # draw if favourited
                if index.data(app_constants.FAV_ROLE):
                    star_ribbon_w = w * 0.1
                    star_ribbon_l = w * 0.08
                    rib_top_1 = QPointF(x + star_ribbon_l, y)
                    rib_side_1 = QPointF(x, y + star_ribbon_l)
                    rib_top_2 = QPointF(x + star_ribbon_l + star_ribbon_w, y)
                    rib_side_2 = QPointF(x, y + star_ribbon_l + star_ribbon_w)
                    rib_star_mid_1 = QPointF((rib_top_1.x() + rib_side_1.x()) / 2, (rib_top_1.y() + rib_side_1.y()) / 2)
                    rib_star_factor = star_ribbon_l / 4
                    rib_star_p1_1 = rib_star_mid_1 + QPointF(rib_star_factor, -rib_star_factor)
                    rib_star_p1_2 = rib_star_p1_1 + QPointF(-rib_star_factor, -rib_star_factor)
                    rib_star_p1_3 = rib_star_mid_1 + QPointF(-rib_star_factor, rib_star_factor)
                    rib_star_p1_4 = rib_star_p1_3 + QPointF(-rib_star_factor, -rib_star_factor)

                    crown_1 = QPolygonF([rib_star_p1_1, rib_star_p1_2, rib_star_mid_1, rib_star_p1_4, rib_star_p1_3])
                    painter.setBrush(QBrush(QColor(255, 255, 0, 200)))
                    painter.drawPolygon(crown_1)

                    ribbon_polygon = QPolygonF([rib_top_1, rib_side_1, rib_side_2, rib_top_2])
                    ribbon_path = QPainterPath()
                    ribbon_path.setFillRule(Qt.WindingFill)
                    ribbon_path.addPolygon(ribbon_polygon)
                    ribbon_path.closeSubpath()
                    painter.drawPath(ribbon_path)
                    painter.setPen(QColor(255, 0, 0, 100))
                    painter.drawPolyline(rib_top_1, rib_star_p1_1, rib_star_p1_2, rib_star_mid_1, rib_star_p1_4, rib_star_p1_3, rib_side_1)
                    painter.drawLine(rib_top_1, rib_top_2)
                    painter.drawLine(rib_top_2, rib_side_2)
                    painter.drawLine(rib_side_1, rib_side_2)
                painter.restore()

                if self._paint_level > 0:
                    #type_w = painter.fontMetrics().width(gallery.file_type)
                    #type_h = painter.fontMetrics().height()
                    #type_p = QPoint(x + 4, y + app_constants.THUMB_H_SIZE - type_h - 5)
                    #type_rect = QRect(type_p.x() - 2, type_p.y() - 1, type_w + 4, type_h + 1)
                    #if app_constants.DISPLAY_GALLERY_TYPE:
                    #    type_color = QColor(239, 0, 0, 200)
                    #    if gallery.file_type == "zip":
                    #        type_color = QColor(241, 0, 83, 200)
                    #    elif gallery.file_type == "cbz":
                    #        type_color = QColor(0, 139, 0, 200)
                    #    elif gallery.file_type == "rar":
                    #        type_color = QColor(30, 127, 150, 200)
                    #    elif gallery.file_type == "cbr":
                    #        type_color = QColor(210, 0, 13, 200)

                    #    painter.save()
                    #    painter.setPen(QPen(Qt.white))
                    #    painter.fillRect(type_rect, type_color)
                    #    painter.drawText(type_p.x(), type_p.y() + painter.fontMetrics().height() - 4, gallery.file_type)
                    #    painter.restore()
                

                    if app_constants.DISPLAY_RATING and index.data(app_constants.RATING_ROLE):
                        star_start_x = type_rect.x()+type_rect.width() if app_constants.DISPLAY_GALLERY_TYPE else x
                        star_width = star_rating.sizeHint().width()
                        star_start_x += ((x+w-star_start_x)-(star_width))/2
                        star_rating.paint(painter,
                            QRect(star_start_x, type_rect.y(), star_width, type_rect.height()))

                #if gallery.state == app_constants.GalleryState.New:
                #    painter.save()
                #    painter.setPen(Qt.NoPen)
                #    gradient = QLinearGradient()
                #    gradient.setStart(x, y + app_constants.THUMB_H_SIZE / 2)
                #    gradient.setFinalStop(x, y + app_constants.THUMB_H_SIZE)
                #    gradient.setColorAt(0, QColor(255, 255, 255, 0))
                #    gradient.setColorAt(1, QColor(0, 255, 0, 150))
                #    painter.setBrush(QBrush(gradient))
                #    painter.drawRoundedRect(QRectF(x, y + app_constants.THUMB_H_SIZE / 2, w, app_constants.THUMB_H_SIZE / 2), 2, 2)
                #    painter.restore()

                def draw_text_label(lbl_h):
                    #draw the label for text
                    painter.save()
                    painter.translate(x, y + app_constants.THUMB_H_SIZE)
                    box_color = QBrush(QColor(label_color))#QColor(0,0,0,123))
                    painter.setBrush(box_color)
                    rect = QRect(0, 0, w, lbl_h) #x, y, width, height
                    painter.fillRect(rect, box_color)
                    painter.restore()
                    return rect

                if option.state & QStyle.State_MouseOver or \
                    option.state & QStyle.State_Selected:
                    title_layout = misc.text_layout(title, w, self.title_font, self.title_font_m)
                    artist_layout = misc.text_layout(artist, w, self.artist_font, self.artist_font_m)
                    t_h = title_layout.boundingRect().height()
                    a_h = artist_layout.boundingRect().height()

                    if app_constants.GALLERY_FONT_ELIDE:
                        lbl_rect = draw_text_label(min(t_h + a_h + 3, app_constants.GRIDBOX_LBL_H))
                    else:
                        lbl_rect = draw_text_label(app_constants.GRIDBOX_LBL_H)

                    clipping = QRectF(x, y + app_constants.THUMB_H_SIZE, w, app_constants.GRIDBOX_LBL_H - 10)
                    painter.setPen(QColor(title_color))
                    title_layout.draw(painter, QPointF(x, y + app_constants.THUMB_H_SIZE),
                          clip=clipping)
                    painter.setPen(QColor(artist_color))
                    artist_layout.draw(painter, QPointF(x, y + app_constants.THUMB_H_SIZE + t_h),
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
                    painter.translate(x, y + app_constants.THUMB_H_SIZE)
                    if app_constants.GALLERY_FONT_ELIDE:
                        painter.setFont(self.title_font)
                        painter.setPen(QColor(title_color))
                        painter.drawText(title_rect,
                                 self.title_font_m.elidedText(title, Qt.ElideRight, w - 10),
                                 alignment)
                
                        painter.setPen(QColor(artist_color))
                        painter.setFont(self.artist_font)
                        alignment.setWrapMode(QTextOption.NoWrap)
                        painter.drawText(artist_rect,
                                    self.title_font_m.elidedText(artist, Qt.ElideRight, w - 10),
                                    alignment)
                    else:
                        text_area.setDefaultFont(QFont(self.font_name))
                        text_area.drawContents(painter)
                    ##painter.resetTransform()
                    painter.restore()

                if option.state & QStyle.State_Selected:
                    painter.save()
                    selected_rect = QRectF(x, y, w, lbl_rect.height() + app_constants.THUMB_H_SIZE)
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QBrush(QColor(164,164,164,120)))
                    painter.drawRoundedRect(selected_rect, 5, 5)
                    #painter.fillRect(selected_rect, QColor(164,164,164,120))
                    painter.restore()

                def warning(txt):
                    painter.save()
                    selected_rect = QRectF(x, y, w, lbl_rect.height() + app_constants.THUMB_H_SIZE)
                    painter.setPen(Qt.NoPen)
                    painter.setBrush(QBrush(QColor(255,0,0,120)))
                    p_path = QPainterPath()
                    p_path.setFillRule(Qt.WindingFill)
                    p_path.addRoundedRect(selected_rect, 5,5)
                    p_path.addRect(x,y, 20, 20)
                    p_path.addRect(x + w - 20,y, 20, 20)
                    painter.drawPath(p_path.simplified())
                    painter.setPen(QColor("white"))
                    txt_layout = misc.text_layout(txt, w, self.title_font, self.title_font_m)
                    txt_layout.draw(painter, QPointF(x, y + h * 0.3))
                    painter.restore()

                if not index.data(app_constants.ITEM_ROLE).id and self.view.view_type != app_constants.ViewType.Addition:
                    warning("This gallery does not exist anymore!")
                #elif gallery.dead_link:
                #    warning("Cannot find gallery source!")


                if app_constants.DEBUG or self.view.view_type == app_constants.ViewType.Duplicate:
                    painter.save()
                    painter.setPen(QPen(Qt.white))
                    id_txt = "ID: {}".format(index.data(app_constants.ITEM_ROLE).id)
                    type_w = painter.fontMetrics().width(id_txt)
                    type_h = painter.fontMetrics().height()
                    type_p = QPoint(x + 4, y + 50 - type_h - 5)
                    type_rect = QRect(type_p.x() - 2, type_p.y() - 1, type_w + 4, type_h + 1)
                    painter.fillRect(type_rect, QColor(239, 0, 0, 200))
                    painter.drawText(type_p.x(), type_p.y() + painter.fontMetrics().height() - 4, id_txt)
                    painter.restore()

                if option.state & QStyle.State_Selected:
                    painter.setPen(QPen(option.palette.highlightedText().color()))
            else:
                painter.fillRect(option.rect, QColor(164,164,164,100))
                painter.setPen(QColor(164,164,164,200))
                txt_layout = misc.text_layout("Fetching...", w, self.title_font, self.title_font_m)

                clipping = QRectF(x, y + h // 4, w, app_constants.GRIDBOX_LBL_H - 10)
                txt_layout.draw(painter, QPointF(x, y + h // 4),
                        clip=clipping)
        else:
            super().paint(painter, option, index)

    def _ribbon_color(self, gallery_type):
        if gallery_type:
            gallery_type = gallery_type.lower()
        if gallery_type == "manga":
            return app_constants.GRID_VIEW_T_MANGA_COLOR
        elif gallery_type == "doujinshi":
            return app_constants.GRID_VIEW_T_DOUJIN_COLOR
        elif "artist cg" in gallery_type:
            return app_constants.GRID_VIEW_T_ARTIST_CG_COLOR
        elif "game cg" in gallery_type:
            return app_constants.GRID_VIEW_T_GAME_CG_COLOR
        elif gallery_type == "western":
            return app_constants.GRID_VIEW_T_WESTERN_COLOR
        elif "image" in gallery_type:
            return app_constants.GRID_VIEW_T_IMAGE_COLOR
        elif gallery_type == "non-h":
            return app_constants.GRID_VIEW_T_NON_H_COLOR
        elif gallery_type == "cosplay":
            return app_constants.GRID_VIEW_T_COSPLAY_COLOR
        else:
            return app_constants.GRID_VIEW_T_OTHER_COLOR

    def sizeHint(self, option, index):
        return QSize(self.W, self.H)

class GridView(QListView):
    """
    Grid View
    """

    STATUS_BAR_MSG = pyqtSignal(str)

    def __init__(self, model, v_type, filter_model=None, parent=None):
        super().__init__(parent)
        self.parent_widget = parent
        self.view_type = v_type
        self.setViewMode(self.IconMode)
        self.setResizeMode(self.Adjust)
        self.setWrapping(True)
        # all items have the same size (perfomance)
        #self.setUniformItemSizes(True)
        # improve scrolling
        self.setAutoScroll(True)
        self.setVerticalScrollMode(self.ScrollPerPixel)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setLayoutMode(self.Batched)
        self.setMouseTracking(True)
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.viewport().setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(self.DragDrop)
        self.sort_model = filter_model if filter_model else SortFilterModel(self)
        self.grid_delegate = GalleryDelegate(parent, self)
        self.setItemDelegate(self.grid_delegate)
        self.setSpacing(app_constants.GRID_SPACING)
        self.setFlow(QListView.LeftToRight)
        self.setIconSize(QSize(self.grid_delegate.W, self.grid_delegate.H))
        self.setSelectionBehavior(self.SelectItems)
        self.setSelectionMode(self.ExtendedSelection)
        self.gallery_model = model
        #self.sort_model.change_model(self.gallery_model)
        #self.sort_model.sort(0)
        self.setModel(self.gallery_model)
        self.setViewportMargins(0,0,0,0)

        #self.gallery_window = misc.GalleryMetaWindow(parent if parent else self)
        #self.gallery_window.arrow_size = (10,10,)
        #self.clicked.connect(lambda idx: self.gallery_window.show_gallery(idx, self))

        self.current_sort = app_constants.CURRENT_SORT
        #if self.view_type == app_constants.ViewType.Duplicate:
        #    self.sort_model.setSortRole(GalleryModel.TIME_ROLE)
        #else:
        #    self.sort(self.current_sort)
        if app_constants.DEBUG:
            def debug_print(a):
                g = a.data(app_constants.ITEM_ROLE)
                try:
                    print(g)
                except:
                    print("{}".format(g).encode(errors='ignore'))
                #log_d(gallerydb.HashDB.gen_gallery_hash(g, 0, 'mid')['mid'])

            self.clicked.connect(debug_print)

        self.k_scroller = QScroller.scroller(self)
        self._scroll_speed_timer = QTimer(self)
        self._scroll_speed_timer.timeout.connect(self._calculate_scroll_speed)
        self._scroll_speed_timer.setInterval(500) # ms
        self._old_scroll_value = 0
        self._scroll_zero_once = True
        self._scroll_speed = 0
        self._scroll_speed_timer.start()

    @property
    def scroll_speed(self):
        return self._scroll_speed

    def _calculate_scroll_speed(self):
        new_value = self.verticalScrollBar().value()
        self._scroll_speed = abs(self._old_scroll_value - new_value)
        self._old_scroll_value = new_value
        
        if self.verticalScrollBar().value() in (0, self.verticalScrollBar().maximum()):
            self._scroll_zero_once = True

        if self._scroll_zero_once:
            self.update()
            self._scroll_zero_once = False

        # update view if not scrolling
        if new_value < 400 and self._old_scroll_value > 400:
            self.update()


    def get_visible_indexes(self, column=0):
        "find all galleries in viewport"
        gridW = self.grid_delegate.W + app_constants.GRID_SPACING * 2
        gridH = self.grid_delegate.H + app_constants.GRID_SPACING * 2
        region = self.viewport().visibleRegion()
        idx_found = []

        def idx_is_visible(idx):
            idx_rect = self.visualRect(idx)
            return region.contains(idx_rect) or region.intersects(idx_rect)

        #get first index
        first_idx = self.indexAt(QPoint(gridW // 2, 0)) # to get indexes on the way out of view
        if not first_idx.isValid():
            first_idx = self.indexAt(QPoint(gridW // 2, gridH // 2))

        if first_idx.isValid():
            nxt_idx = first_idx
            # now traverse items until index isn't visible
            while(idx_is_visible(nxt_idx)):
                idx_found.append(nxt_idx)
                nxt_idx = nxt_idx.sibling(nxt_idx.row() + 1, column)
            
        return idx_found

    def wheelEvent(self, event):
        if self.gallery_window.isVisible():
            self.gallery_window.hide_animation.start()
        return super().wheelEvent(event)

    def mouseMoveEvent(self, event):
        #self.gallery_window.mouseMoveEvent(event)
        return super().mouseMoveEvent(event)

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            s_idx = self.selectedIndexes()
            if s_idx:
                for idx in s_idx:
                    self.doubleClicked.emit(idx)
        elif event.modifiers() == Qt.ShiftModifier and event.key() == Qt.Key_Delete:
            CommonView.remove_selected(self, True)
        elif event.key() == Qt.Key_Delete:
            CommonView.remove_selected(self)
        return super().keyPressEvent(event)

    def favorite(self, index):
        assert isinstance(index, QModelIndex)
        gallery = index.data(Qt.UserRole + 1)
        if gallery.fav == 1:
            gallery.fav = 0
            #self.model().replaceRows([gallery], index.row(), 1, index)
            gallerydb.execute(gallerydb.GalleryDB.modify_gallery, True, gallery.id, {'fav':0})
            self.gallery_model.CUSTOM_STATUS_MSG.emit("Unfavorited")
        else:
            gallery.fav = 1
            #self.model().replaceRows([gallery], index.row(), 1, index)
            gallerydb.execute(gallerydb.GalleryDB.modify_gallery, True, gallery.id, {'fav':1})
            self.gallery_model.CUSTOM_STATUS_MSG.emit("Favorited")

    def del_chapter(self, index, chap_numb):
        gallery = index.data(Qt.UserRole + 1)
        if len(gallery.chapters) < 2:
            CommonView.remove_gallery(self, [index])
        else:
            msgbox = QMessageBox(self)
            msgbox.setText('Are you sure you want to delete:')
            msgbox.setIcon(msgbox.Question)
            msgbox.setInformativeText('Chapter {} of {}'.format(chap_numb + 1,
                                                          gallery.title))
            msgbox.setStandardButtons(msgbox.Yes | msgbox.No)
            if msgbox.exec() == msgbox.Yes:
                gallery.chapters.pop(chap_numb, None)
                self.gallery_model.replaceRows([gallery], index.row())
                gallerydb.execute(gallerydb.ChapterDB.del_chapter, True, gallery.id, chap_numb)

    def sort(self, name):
        if not self.view_type == app_constants.ViewType.Duplicate:
            if name == 'title':
                self.sort_model.setSortRole(Qt.DisplayRole)
                self.sort_model.sort(0, Qt.AscendingOrder)
                self.current_sort = 'title'
            elif name == 'artist':
                self.sort_model.setSortRole(GalleryModel.ARTIST_ROLE)
                self.sort_model.sort(0, Qt.AscendingOrder)
                self.current_sort = 'artist'
            elif name == 'date_added':
                self.sort_model.setSortRole(GalleryModel.DATE_ADDED_ROLE)
                self.sort_model.sort(0, Qt.DescendingOrder)
                self.current_sort = 'date_added'
            elif name == 'pub_date':
                self.sort_model.setSortRole(GalleryModel.PUB_DATE_ROLE)
                self.sort_model.sort(0, Qt.DescendingOrder)
                self.current_sort = 'pub_date'
            elif name == 'times_read':
                self.sort_model.setSortRole(GalleryModel.TIMES_READ_ROLE)
                self.sort_model.sort(0, Qt.DescendingOrder)
                self.current_sort = 'times_read'
            elif name == 'last_read':
                self.sort_model.setSortRole(GalleryModel.LAST_READ_ROLE)
                self.sort_model.sort(0, Qt.DescendingOrder)
                self.current_sort = 'last_read'

    def contextMenuEvent(self, event):
        CommonView.contextMenuEvent(self, event)

    def updateGeometries(self):
        super().updateGeometries()
        self.verticalScrollBar().setSingleStep(app_constants.SCROLL_SPEED)

class MangaTableView(QTableView):
    STATUS_BAR_MSG = pyqtSignal(str)

    def __init__(self, v_type, parent=None):
        super().__init__(parent)
        self.view_type = v_type

        # options
        self.parent_widget = parent
        self.setAcceptDrops(True)
        self.setDragEnabled(True)
        self.viewport().setAcceptDrops(True)
        self.setDropIndicatorShown(True)
        self.setDragDropMode(self.DragDrop)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setSelectionBehavior(self.SelectRows)
        self.setSelectionMode(self.ExtendedSelection)
        self.setShowGrid(True)
        self.setSortingEnabled(True)
        h_header = self.horizontalHeader()
        h_header.setSortIndicatorShown(True)
        v_header = self.verticalHeader()
        v_header.sectionResizeMode(QHeaderView.Fixed)
        v_header.setDefaultSectionSize(24)
        v_header.hide()
        palette = self.palette()
        palette.setColor(palette.Highlight, QColor(88, 88, 88, 70))
        palette.setColor(palette.HighlightedText, QColor('black'))
        self.setPalette(palette)
        self.setIconSize(QSize(0,0))
        self.doubleClicked.connect(lambda idx: idx.data(Qt.UserRole + 1).chapters[0].open())
        self.grabGesture(Qt.SwipeGesture)
        self.k_scroller = QScroller.scroller(self)

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

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            s_idx = self.selectionModel().selectedRows()
            if s_idx:
                for idx in s_idx:
                    self.doubleClicked.emit(idx)
        elif event.modifiers() == Qt.ShiftModifier and event.key() == Qt.Key_Delete:
            CommonView.remove_selected(self, True)
        elif event.key() == Qt.Key_Delete:
            CommonView.remove_selected(self)
        return super().keyPressEvent(event)

    def contextMenuEvent(self, event):
        CommonView.contextMenuEvent(self, event)

class CommonView:
    """
    Contains identical view implentations
    """

    @staticmethod
    def remove_selected(view_cls, source=False):
        s_indexes = []
        if isinstance(view_cls, QListView):
            s_indexes = view_cls.selectedIndexes()
        elif isinstance(view_cls, QTableView):
            s_indexes = view_cls.selectionModel().selectedRows()

        CommonView.remove_gallery(view_cls, s_indexes, source)

    @staticmethod
    def remove_gallery(view_cls, index_list, local=False):
        #view_cls.sort_model.setDynamicSortFilter(False)
        msgbox = QMessageBox(view_cls)
        msgbox.setIcon(msgbox.Question)
        msgbox.setStandardButtons(msgbox.Yes | msgbox.No)
        if len(index_list) > 1:
            if not local:
                msg = 'Are you sure you want to remove {} selected galleries?'.format(len(index_list))
            else:
                msg = 'Are you sure you want to remove {} selected galleries and their files/directories?'.format(len(index_list))

            msgbox.setText(msg)
        else:
            if not local:
                msg = 'Are you sure you want to remove this gallery?'
            else:
                msg = 'Are you sure you want to remove this gallery and its file/directory?'
            msgbox.setText(msg)

        if msgbox.exec() == msgbox.Yes:
            #view_cls.setUpdatesEnabled(False)
            gallery_list = []
            gallery_db_list = []
            log_i('Removing {} galleries'.format(len(index_list)))
            for index in index_list:
                gallery = index.data(Qt.UserRole + 1)
                gallery_list.append(gallery)
                log_i('Attempt to remove: {} by {}'.format(gallery.title.encode(errors="ignore"),
                                            gallery.artist.encode(errors="ignore")))
                if gallery.id:
                    gallery_db_list.append(gallery)
            gallerydb.execute(gallerydb.GalleryDB.del_gallery, True, gallery_db_list, local=local, priority=0)

            rows = len(gallery_list)
            view_cls.gallery_model._gallery_to_remove.extend(gallery_list)
            view_cls.gallery_model.removeRows(view_cls.gallery_model.rowCount() - rows, rows)

            #view_cls.STATUS_BAR_MSG.emit('Gallery removed!')
            #view_cls.setUpdatesEnabled(True)
        #view_cls.sort_model.setDynamicSortFilter(True)

    @staticmethod
    def find_index(view_cls, gallery_id, sort_model=False):
        "Finds and returns the index associated with the gallery id"
        index = None
        model = view_cls.sort_model if sort_model else view_cls.gallery_model
        rows = model.rowCount()
        for r in range(rows):
            indx = model.index(r, 0)
            m_gallery = indx.data(Qt.UserRole + 1)
            if m_gallery.id == gallery_id:
                index = indx
                break
        return index

    @staticmethod
    def open_random_gallery(view_cls):
        try:
            g = random.randint(0, view_cls.sort_model.rowCount() - 1)
        except ValueError:
            return
        indx = view_cls.sort_model.index(g, 1)
        chap_numb = 0
        if app_constants.OPEN_RANDOM_GALLERY_CHAPTERS:
            gallery = indx.data(Qt.UserRole + 1)
            b = len(gallery.chapters)
            if b > 1:
                chap_numb = random.randint(0, b - 1)

        CommonView.scroll_to_index(view_cls, view_cls.sort_model.index(indx.row(), 0))
        indx.data(Qt.UserRole + 1).chapters[chap_numb].open()

    @staticmethod
    def scroll_to_index(view_cls, idx, select=True):
        old_value = view_cls.verticalScrollBar().value()
        view_cls.setAutoScroll(False)
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
        view_cls.setAutoScroll(True)
        view_cls.update()

    @staticmethod
    def contextMenuEvent(view_cls, event):
        grid_view = False
        table_view = False
        if isinstance(view_cls, QListView):
            grid_view = True
        elif isinstance(view_cls, QTableView):
            table_view = True

        handled = False
        index = view_cls.indexAt(event.pos())
        index = view_cls.sort_model.mapToSource(index)

        selected = False
        if table_view:
            s_indexes = view_cls.selectionModel().selectedRows()
        else:
            s_indexes = view_cls.selectedIndexes()
        select_indexes = []
        for idx in s_indexes:
            if idx.isValid() and idx.column() == 0:
                select_indexes.append(view_cls.sort_model.mapToSource(idx))
        if len(select_indexes) > 1:
            selected = True

        if index.isValid():
            if grid_view:
                if view_cls.gallery_window.isVisible():
                    view_cls.gallery_window.hide_animation.start()
                view_cls.grid_delegate.CONTEXT_ON = True
            if selected:
                menu = misc.GalleryMenu(view_cls, index, view_cls.sort_model,
                               view_cls.parent_widget, select_indexes)
            else:
                menu = misc.GalleryMenu(view_cls, index, view_cls.sort_model,
                               view_cls.parent_widget)
            menu.delete_galleries.connect(lambda s: CommonView.remove_gallery(view_cls, select_indexes, s))
            menu.edit_gallery.connect(CommonView.spawn_dialog)
            handled = True

        if handled:
            menu.exec_(event.globalPos())
            if grid_view:
                view_cls.grid_delegate.CONTEXT_ON = False
            event.accept()
            del menu
        else:
            event.ignore()

    @staticmethod
    def spawn_dialog(app_inst, gallery=None):
        dialog = gallerydialog.GalleryDialog(app_inst, gallery)
        dialog.show()

class PathView(QWidget):

    HEIGHT = 22

    def __init__(self, view, parent=None):
        super().__init__(parent)
        self.view = view
        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        top_layout = QHBoxLayout()

        persistent_layout = QHBoxLayout()
        top_layout.addLayout(persistent_layout)

        self.idxs = {}

        self.home_btn = QPushButton("Home")
        self.home_btn.clicked.connect(lambda: self.update_path(QModelIndex()))
        self.home_btn.adjustSize()
        self.home_btn.setFixedSize(self.home_btn.width(), self.HEIGHT)
        self.home_btn.setStyleSheet("border:0; border-radius:0;")
        persistent_layout.addWidget(self.home_btn)

        self.path_layout = QHBoxLayout()
        top_layout.addLayout(self.path_layout, 1)
        self.path_layout.setAlignment(Qt.AlignLeft)
        main_layout.addLayout(top_layout)
        main_layout.addWidget(view)
        self.install_to_view(view)

    def add_arrow(self):
        arrow = QLabel(">")
        arrow.adjustSize()
        arrow.setFixedWidth(arrow.width())
        arrow.setFixedHeight(self.HEIGHT)
        arrow.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self.path_layout.insertWidget(0, arrow, Qt.AlignLeft)

    def add_item(self, idx):
        path_bar = QPushButton(idx.data(Qt.DisplayRole))
        path_bar.setStyleSheet("border:0; border-radius:0;")
        path_bar.setFixedHeight(self.HEIGHT)
        path_bar.adjustSize()
        path_bar.setFixedWidth(path_bar.width())
        path_bar.clicked.connect(lambda: self.view.doubleClicked.emit(idx))
        
        self.path_layout.insertWidget(0, path_bar, Qt.AlignLeft)

    def update_path(self, idx):
        if not (idx.isValid() and not idx.child(0,0).isValid()):
            self.view.setRootIndex(idx)
        misc.clearLayout(self.path_layout)
        self.idxs.clear()
        parent = idx
        while parent.isValid():
            if parent.data(app_constants.QITEM_ROLE).type() != PageItem.type():
                self.add_item(parent)
                self.add_arrow()
            parent = parent.parent()

    def install_to_view(self, view):
        view.doubleClicked.connect(self.update_path)

class ViewManager:

    gallery_views = []
    
    @enum.unique
    class View(enum.Enum):
        List = 1
        Table = 2

    def __init__(self, v_type, parent, allow_sidebarwidget=False):
        self.allow_sidebarwidget = allow_sidebarwidget
        self._delete_proxy_model = None

        self.view_type = v_type

        if v_type == app_constants.ViewType.Default:
            model = GalleryModel(app_constants.GALLERY_DATA, parent)
        elif v_type == app_constants.ViewType.Addition:
            model = GalleryModel(app_constants.GALLERY_ADDITION_DATA, parent)
        elif v_type == app_constants.ViewType.Duplicate:
            model = GalleryModel([], parent)

        #list view
        self.list_view = GridView(self.create_model(), v_type, parent=parent)
        #self.list_view.sort_model.setup_search()
        self.sort_model = self.list_view.sort_model
        self.gallery_model = self.list_view.gallery_model

        self.view_layout = QStackedLayout()
        self.m_l_view_index = self.view_layout.addWidget(PathView(self.list_view))

        self.current_view = self.View.List
        self.gallery_views.append(self)

        if v_type in (app_constants.ViewType.Default, app_constants.ViewType.Addition):
            self.sort_model.enable_drag = True

    def create_model(self):
        model = QStandardItemModel()
        parent = model.invisibleRootItem()
        gns = db.GalleryNamespace(name="A Gallery Namespace")
        gartists = [db.Artist(name="Artist"+str(x)) for x in range(2)]
        for x in range(10):
            coll = db.Collection(title="Collection "+str(x))
            coll.profile = os.path.join(db_constants.THUMBNAIL_PATH, "thumb2.png")
            coll.info = "A lonely collection"
            pitem = CollectionItem(coll)
            parent.appendRow(pitem)
            for y in range(20):
                gall = db.Gallery(title="Gallery "+str(y))
                gall.profile = os.path.join(db_constants.THUMBNAIL_PATH, "thumb.png")
                gall.path = "C:/hello"
                gall.info = "A lonely girl"
                gall.fav = True if y % 2 == 0 else False
                gall.type = "Doujinshi"
                gall.language = "English"
                gall.rating = 5
                gall.times_read = 20
                gall.status = "Finished"
                gall.pub_date = datetime.date.today()
                gall.last_read = datetime.datetime.now()
                gall.parent = gns
                gall.urls.extend([db.GalleryUrl(url="www.hello.com") for x in range(2)])
                gall.artists.extend(gartists)

                gitem = GalleryItem(gall)
                pitem.appendRow(gitem)
                for z in range(30):
                    page = db.Page(number=z)
                    page.profile = os.path.join(db_constants.THUMBNAIL_PATH, "thumb3.png")
                    gitem.appendRow(PageItem(page))
        return model

    def _delegate_delete(self):
        if self._delete_proxy_model:
            gs = [g for g in self.gallery_model._gallery_to_remove]
            self._delete_proxy_model._gallery_to_remove = gs
            self._delete_proxy_model.removeRows(self._delete_proxy_model.rowCount() - len(gs), len(gs))

    def set_delete_proxy(self, other_model):
        self._delete_proxy_model = other_model
        self.gallery_model.rowsAboutToBeRemoved.connect(self._delegate_delete, Qt.DirectConnection)

    def add_gallery(self, gallery, db=False, record_time=False):
        if isinstance(gallery, (list, tuple)):
            for g in gallery:
                g.view = self.view_type
                if self.view_type != app_constants.ViewType.Duplicate:
                    g.state = app_constants.GalleryState.New
                if db:
                    gallerydb.execute(gallerydb.GalleryDB.add_gallery, True, g)
                else:
                    if not g.profile:
                        Executors.generate_thumbnail(g, on_method=g.set_profile)
            rows = len(gallery)
            self.list_view.gallery_model._gallery_to_add.extend(gallery)
            if record_time:
                g.qtime = QTime.currentTime()
        else:
            gallery.view = self.view_type
            if self.view_type != app_constants.ViewType.Duplicate:
                gallery.state = app_constants.GalleryState.New
            rows = 1
            self.list_view.gallery_model._gallery_to_add.append(gallery)
            if record_time:
                g.qtime = QTime.currentTime()
            if db:
                gallerydb.execute(gallerydb.GalleryDB.add_gallery, True, gallery)
            else:
                if not gallery.profile:
                    Executors.generate_thumbnail(gallery, on_method=gallery.set_profile)
        self.list_view.gallery_model.insertRows(self.list_view.gallery_model.rowCount(), rows)
        
    def replace_gallery(self, list_of_gallery, db_optimize=True):
        "Replaces the view and DB with given list of gallery, at given position"
        assert isinstance(list_of_gallery, (list, gallerydb.Gallery)), "Please pass a gallery to replace with"
        if isinstance(list_of_gallery, gallerydb.Gallery):
            list_of_gallery = [list_of_gallery]
        log_d('Replacing {} galleries'.format(len(list_of_gallery)))
        if db_optimize:
            gallerydb.execute(gallerydb.GalleryDB.begin, True)
        for gallery in list_of_gallery:
            kwdict = {'title':gallery.title,
             'profile':gallery.profile,
             'artist':gallery.artist,
             'info':gallery.info,
             'type':gallery.type,
             'language':gallery.language,
             'rating':gallery.rating,
             'status':gallery.status,
             'pub_date':gallery.pub_date,
             'tags':gallery.tags,
             'link':gallery.link,
             'series_path':gallery.path,
             'chapters':gallery.chapters,
             'exed':gallery.exed}

            gallerydb.execute(gallerydb.GalleryDB.modify_gallery,
                             True, gallery.id, **kwdict)
        if db_optimize:
            gallerydb.execute(gallerydb.GalleryDB.end, True)

    def changeTo(self, idx):
        "change view"
        self.view_layout.setCurrentIndex(idx)
        if idx == self.m_l_view_index:
            self.current_view = self.View.List
        elif idx == self.m_t_view_index:
            self.current_view = self.View.Table

    def get_current_view(self):
        if self.current_view == self.View.List:
            return self.list_view
        else:
            return self.table_view

    def fav_is_current(self):
        if self.table_view.sort_model.current_view == \
            self.table_view.sort_model.CAT_VIEW:
            return False
        return True

    def hide(self):
        self.view_layout.currentWidget().hide()

    def show(self):
        self.view_layout.currentWidget().show()

if __name__ == '__main__':
    raise NotImplementedError("Unit testing not yet implemented")
