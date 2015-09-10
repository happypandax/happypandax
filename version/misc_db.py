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
							 QVBoxLayout, QTabWidget, QAction, QGraphicsScene)
from PyQt5.QtCore import Qt

import gallerydb

class TagsTreeView(QWidget):
	"""
	
	"""
	def __init__(self, parent, window=False):
		if window:
			super().__init__(parent, Qt.Window)
		else:
			super().__init__(parent)
		main_layout = QVBoxLayout(self)
		tabbar = QTabWidget(self)
		main_layout.addWidget(tabbar)
		self.tags_tree = QTreeWidget(self)
		tabbar.addTab(self.tags_tree, 'Tags')
		#self.graphs = QGra

	def setup_tags(self):
		pass

	def setup_graphs(self):
		pass

	def setup_about_db(self):
		pass


