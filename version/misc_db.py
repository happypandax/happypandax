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
							 QVBoxLayout, QToolBar, QAction)
from PyQt5.QtCore import Qt

import gallerydb

class TagsTreeView(QWidget):
	"""
	
	"""
	def __init__(self, parent):
		super().__init__(parent)
		main_layout = QVBoxLayout(self)
		tool_bar = QToolBar(self)
		main_layout.addWidget(tool_bar)
		tool_bar.addAction('First')
		self.tree_widget = QTreeWidget(self)

	def make_window(self):
		self.hide()
		self.setWindowFlags(self.windowFlags()|Qt.Window)
		self.show()
