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

#import matplotlib
#matplotlib.use('Qt5Agg')
#from numpy import arange, sin, pi
#from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
#from matplotlib.figure import Figure
#from matplotlib import pyplot as plt

from PyQt5.QtWidgets import (QTreeWidget, QTreeWidgetItem, QWidget,
							 QVBoxLayout, QTabWidget, QAction, QGraphicsScene,
							 QSizePolicy, QMenu, QAction, QApplication,
							 QListWidget)
from PyQt5.QtCore import (Qt, QTimer, pyqtSignal)
from PyQt5.QtGui import QIcon

import gallerydb
import app_constants
import utils

class TagsTreeView(QTreeWidget):
	def __init__(self, **kwargs):
		self.parent_widget = kwargs.pop('app_window', None)
		super().__init__(**kwargs)
		self.setSelectionBehavior(self.SelectItems)
		self.setSelectionMode(self.ExtendedSelection)
		self.clipboard = QApplication.clipboard()

	def search_tags(self, items):
		if self.parent_widget:
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
			self.parent_widget.search(final_txt)

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
			handled = True

		if handled:
			menu.exec_(event.globalPos())
			event.accept()
			del menu
		else:
			event.ignore()

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

		# Tags tree
		self.tags_tree = TagsTreeView(parent=self, app_window=self.parent_widget)
		self.tags_tree.setHeaderHidden(True)
		tabbar.addTab(self.tags_tree, 'Namespace && Tags')
		self.tags_layout = QVBoxLayout(self.tags_tree)
		if parent.manga_list_view.gallery_model.db_emitter._finished:
			self.setup_tags()
		else:
			parent.manga_list_view.gallery_model.db_emitter.DONE.connect(self.setup_tags)
		
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

	def setup_tags(self):
		self.tags_tree.clear()
		tags = gallerydb.add_method_queue(gallerydb.TagDB.get_ns_tags, False)
		items = []
		for ns in tags:
			top_item = QTreeWidgetItem(self.tags_tree)
			if ns == 'default':
				top_item.setText(0, 'No namespace')
			else:
				top_item.setText(0, ns)
			for tag in tags[ns]:
				child_item = QTreeWidgetItem(top_item)
				child_item.setText(0, tag)
		self.tags_tree.sortItems(0, Qt.AscendingOrder)

	def setup_stats(self):
		pass

	def setup_about_db(self):
		pass

	def closeEvent(self, event):
		self.about_to_close.emit()
		return super().closeEvent(event)

