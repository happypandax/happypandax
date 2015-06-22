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

from PyQt5.QtCore import (Qt, QDate, QPoint, pyqtSignal, QThread,
						  QTimer, QObject, QSize, QRect)
from PyQt5.QtGui import QTextCursor, QIcon, QMouseEvent, QFont, QPixmapCache
from PyQt5.QtWidgets import (QWidget, QProgressBar, QLabel,
							 QVBoxLayout, QHBoxLayout,
							 QDialog, QGridLayout, QLineEdit,
							 QFormLayout, QPushButton, QTextEdit,
							 QComboBox, QDateEdit, QGroupBox,
							 QDesktopWidget, QMessageBox, QFileDialog,
							 QCompleter, QListWidgetItem,
							 QListWidget, QApplication, QSizePolicy,
							 QCheckBox, QFrame, QListView,
							 QAbstractItemView, QTreeView, QSpinBox,
							 QAction, QStackedLayout, QTabWidget,
							 QGridLayout, QScrollArea, QLayout, QButtonGroup,
							 QRadioButton)

import os, threading, queue, time, logging
from datetime import datetime
from . import gui_constants
from ..utils import tag_to_string, tag_to_dict, title_parser, ARCHIVE_FILES
from ..database import gallerydb, fetch, db
from .. import settings

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical

#class ErrorEvent(QObject):
#	ERROR_MSG = pyqtSignal(str)
#	DONE = pyqtSignal()
#	def __init__(self):
#		super().__init__()

#	def error_event(self):
#		err_q = db.ErrorQueue
#		while True:
#			msg = err_q.get()
#			ERROR_MSG.emit(msg)
#		DONE.emit()

#class ExceptionHandler(QObject):
#	def __init__(self):
#		super().__init__()
#		thread = QThread()

#		def thread_deleteLater():
#			thread.deleteLater

#		err_instance = ErrorEvent()
#		err_instance.moveToThread(thread)
#		err_instance.ERROR_MSG.connect(self.exception_handler)
#		thread.started.connect(err_instance.error_event)
#		err_instance.DONE.connect(thread.deleteLater)
#		thread.start()

#	def exception_handler(self, msg):
#		"Spawns a dialog with the specified msg"
#		db_msg = msg = "The database is not compatible with the current version of the program"
#		msgbox = QMessageBox()
#		if msg == db_msg:
#			msgbox.setText(msg)
#			msgbox.setStandardButtons(QMessageBox.Ok | QMessageBox.Abort)
#			msgbox.setDefaultButton(QMessageBox.Ok)
#			if msgbox.exec() == QMessageBox.Ok:
#				return True
#		else:
#			msgbox.setText(msg)
#			msgbox.setStandardButtons(QMessageBox.Close)
#			msgbox.setDefaultButton(QMessageBox.Close)
#			if msgbox.exec():
#				exit()

#errors = ExceptionHandler()

#def center_parent(parent, child):
#	"centers child window in parent"
#	centerparent = QPoint(
#			parent.x() + (parent.frameGeometry().width() -
#					 child.frameGeometry().width())//2,
#					parent.y() + (parent.frameGeometry().width() -
#					   child.frameGeometry().width())//2)
#	desktop = QApplication.desktop()
#	sg_rect = desktop.screenGeometry(desktop.screenNumber(parent))
#	child_frame = child.frameGeometry()

#	if centerparent.x() < sg_rect.left():
#		centerparent.setX(sg_rect.left())
#	elif (centerparent.x() + child_frame.width()) > sg_rect.right():
#		centerparent.setX(sg_rect.right() - child_frame.width())

#	if centerparent.y() < sg_rect.top():
#		centerparent.setY(sg_rect.top())
#	elif (centerparent.y() + child_frame.height()) > sg_rect.bottom():
#		centerparent.setY(sg_rect.bottom() - child_frame.height())

#	child.move(centerparent)

class Spacer(QWidget):
	"""
	To be used as a spacer.
	Default mode is both. Specify mode with string: v, h or both
	"""
	def __init__(self, mode='both', parent=None):
		super().__init__(parent)
		if mode == 'h':
			self.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
		elif mode == 'v':
			self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
		else:
			self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

class FlowLayout(QLayout):
    """
    Standard PyQt examples FlowLayout modified to work with a scollable parent
    """
    
    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)

        #if parent is not None:
        #    self.setMargin(margin)
        self.setSpacing(spacing)

        self.itemList = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self.itemList.append(item)

    def count(self):
        return len(self.itemList)

    def itemAt(self, index):
        if index >= 0 and index < len(self.itemList):
            return self.itemList[index]
        return None

    def takeAt(self, index):
        if index >= 0 and index < len(self.itemList):
            return self.itemList.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientations(Qt.Orientation(0))

    def hasHeightForWidth(self):
        return False

    def heightForWidth(self, width):
        height = self.doLayout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()

        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())

        size += QSize(2 * 0, 2 * 0)
        return size
    
    def doLayout(self, rect, testOnly=False):
        """
        """
        x = rect.x()
        y = rect.y()
        lineHeight = 0

        for item in self.itemList:
            wid = item.widget()
            spaceX = self.spacing() + wid.style().layoutSpacing(QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Horizontal)
            spaceY = self.spacing() + wid.style().layoutSpacing(QSizePolicy.PushButton, QSizePolicy.PushButton, Qt.Vertical)
            nextX = x + item.sizeHint().width() + spaceX
            if nextX - spaceX > rect.right() and lineHeight > 0:
                x = rect.x()
                y = y + lineHeight + spaceY
                nextX = x + item.sizeHint().width() + spaceX
                lineHeight = 0

            if not testOnly:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())

        return y + lineHeight - rect.y()

#class ResizeScrollArea(QScrollArea):
#    """
#    A QScrollArea that propagates the resizing to any FlowLayout children.
#    Code from: http://vfxdebate.com/2014/02/25/a-better-pyqt-flow-layout/
#    """
#    def __init(self, parent=None):  
#        super().__init__(parent)

#    def resizeEvent(self, event):
#        wrapper = self.findChild(QWidget)
#        flow = wrapper.findChild(FlowLayout)
        
#        if wrapper and flow:            
#            width = self.viewport().width()
#            height = flow.heightForWidth(width)
#            size = QSize(width, height)
#            point = self.viewport().rect().topLeft()
#            flow.setGeometry(QRect(point, size))
#            self.viewport().update()

#        super().resizeEvent(event)

#class ScrollingFlowWidget(QWidget):
#    """
#    A resizable and scrollable widget that uses a flow layout.
#    Use its addWidget() method to flow children into it.
#    """
#    def __init__(self,parent=None):
#        super().__init__(parent)
#        grid = QGridLayout(self)
#        scroll = ResizeScrollArea()
#        self._wrapper = QWidget(scroll)
#        self.flowLayout = FlowLayout(self._wrapper)
#        self._wrapper.setLayout(self.flowLayout)
#        scroll.setWidget(self._wrapper)
#        scroll.setWidgetResizable(True)
#        grid.addWidget(scroll)


#    def addWidget(self, widget):
#        self.flowLayout.addWidget(widget)
#        widget.setParent(self._wrapper)

# ----------------------------------------------------------

class LineEdit(QLineEdit):
	"""
	Custom Line Edit which sacrifices contextmenu for selectAll
	"""
	def __init__(self, parent=None):
		super().__init__(parent)

	def mousePressEvent(self, event):
		print('Oh!')
		if event.button() == Qt.RightButton:
			print('Yes')
			self.selectAll()
		else:
			super().mousePressEvent(event)

	def contextMenuEvent(self, QContextMenuEvent):
		pass

class SettingsDialog(QWidget):
	"A settings dialog"
	scroll_speed_changed = pyqtSignal()
	def __init__(self, parent=None):
		super().__init__(parent, flags=Qt.Window)
		self.resize(700, 500)
		self.show()
		self.restore_values()
		self.initUI()

	def initUI(self):
		main_layout = QVBoxLayout()
		sub_layout = QHBoxLayout()
		# Left Panel
		left_panel = QListWidget()
		left_panel.setViewMode(left_panel.ListMode)
		#left_panel.setIconSize(QSize(40,40))
		left_panel.setTextElideMode(Qt.ElideRight)
		left_panel.setMaximumWidth(200)
		left_panel.itemClicked.connect(self.change)
		#web.setText('Web')
		self.web = QListWidgetItem()
		self.web.setText('Web')
		self.visual = QListWidgetItem()
		self.visual.setText('Visual')
		self.advanced = QListWidgetItem()
		self.advanced.setText('Advanced')
		self.about = QListWidgetItem()
		self.about.setText('About')

		#main.setIcon(QIcon(os.path.join(gui_constants.static_dir, 'plus2.png')))
		left_panel.addItem(self.web)
		left_panel.addItem(self.visual)
		left_panel.addItem(self.advanced)
		left_panel.addItem(self.about)
		left_panel.setMaximumWidth(100)

		# right panel
		self.right_panel = QStackedLayout()
		self.init_right_panel()

		# bottom
		bottom_layout = QHBoxLayout()
		ok_btn = QPushButton('Ok')
		ok_btn.clicked.connect(self.accept)
		cancel_btn = QPushButton('Cancel')
		cancel_btn.clicked.connect(self.close)
		info_lbl = QLabel()
		info_lbl.setText('<a href="https://github.com/Pewpews/happypanda">'+
				   'Visit GitHub Repo</a> | Find any bugs? Check out the troubleshoot guide '+
				   'in About section.')
		info_lbl.setTextFormat(Qt.RichText)
		info_lbl.setTextInteractionFlags(Qt.TextBrowserInteraction)
		info_lbl.setOpenExternalLinks(True)
		self.spacer = QWidget()
		self.spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
		bottom_layout.addWidget(info_lbl, 0, Qt.AlignLeft)
		bottom_layout.addWidget(self.spacer)
		bottom_layout.addWidget(ok_btn, 0, Qt.AlignRight)
		bottom_layout.addWidget(cancel_btn, 0, Qt.AlignRight)

		sub_layout.addWidget(left_panel)
		sub_layout.addLayout(self.right_panel)
		main_layout.addLayout(sub_layout)
		main_layout.addLayout(bottom_layout)

		self.restore_options()

		self.setLayout(main_layout)
		self.setWindowTitle('Settings')


	def change(self, item):
		def curr_index(index):
			if index != self.right_panel.currentIndex():
				self.right_panel.setCurrentIndex(index)

		if item == self.web:
			curr_index(self.web_index)
		elif item == self.visual:
			curr_index(self.visual_index)
		elif item == self.advanced:
			curr_index(self.advanced_index)
		elif item == self.about:
			curr_index(self.about_index)

	def restore_values(self):
		#Web
		self.exprops = settings.ExProperties()

		# Visual
		self.high_quality_thumbs = gui_constants.HIGH_QUALITY_THUMBS
		self.popup_width = gui_constants.POPUP_WIDTH
		self.popup_height = gui_constants.POPUP_HEIGHT
		self.style = gui_constants.user_stylesheet_path

		# Advanced
		self.scroll_speed = gui_constants.SCROLL_SPEED
		self.cache_size = gui_constants.THUMBNAIL_CACHE_SIZE
		self.prefetch_item_amnt = gui_constants.PREFETCH_ITEM_AMOUNT

	def restore_options(self):
		# Web / Exhentai
		self.ipbid_edit.setText(self.exprops.ipb_id)
		self.ipbpass_edit.setText(self.exprops.ipb_pass)

		# Visual / Grid View / Tooltip
		self.grid_tooltip_group.setChecked(gui_constants.GRID_TOOLTIP)
		self.visual_grid_tooltip_title.setChecked(gui_constants.TOOLTIP_TITLE)
		self.visual_grid_tooltip_author.setChecked(gui_constants.TOOLTIP_AUTHOR)
		self.visual_grid_tooltip_chapters.setChecked(gui_constants.TOOLTIP_CHAPTERS)
		self.visual_grid_tooltip_status.setChecked(gui_constants.TOOLTIP_STATUS)
		self.visual_grid_tooltip_type.setChecked(gui_constants.TOOLTIP_TYPE)
		self.visual_grid_tooltip_lang.setChecked(gui_constants.TOOLTIP_LANG)
		self.visual_grid_tooltip_descr.setChecked(gui_constants.TOOLTIP_DESCR)
		self.visual_grid_tooltip_tags.setChecked(gui_constants.TOOLTIP_TAGS)
		self.visual_grid_tooltip_last_read.setChecked(gui_constants.TOOLTIP_LAST_READ)
		self.visual_grid_tooltip_times_read.setChecked(gui_constants.TOOLTIP_TIMES_READ)
		self.visual_grid_tooltip_pub_date.setChecked(gui_constants.TOOLTIP_PUB_DATE)
		self.visual_grid_tooltip_date_added.setChecked(gui_constants.TOOLTIP_DATE_ADDED)

		if gui_constants.SEARCH_ON_ENTER:
			self.search_on_enter.setChecked(True)
		else:
			self.search_every_keystroke.setChecked(True)

	def accept(self):
		set = settings.set
		# Web / ExHentai
		self.exprops.ipb_id = self.ipbid_edit.text()
		self.exprops.ipb_pass = self.ipbpass_edit.text()

		# Visual / Grid View / Tooltip
		gui_constants.GRID_TOOLTIP = self.grid_tooltip_group.isChecked()
		set(gui_constants.GRID_TOOLTIP, 'Visual', 'grid tooltip')
		gui_constants.TOOLTIP_TITLE = self.visual_grid_tooltip_title.isChecked()
		set(gui_constants.TOOLTIP_TITLE, 'Visual', 'tooltip title')
		gui_constants.TOOLTIP_AUTHOR = self.visual_grid_tooltip_author.isChecked()
		set(gui_constants.TOOLTIP_AUTHOR, 'Visual', 'tooltip author')
		gui_constants.TOOLTIP_CHAPTERS = self.visual_grid_tooltip_chapters.isChecked()
		set(gui_constants.TOOLTIP_CHAPTERS, 'Visual', 'tooltip chapters')
		gui_constants.TOOLTIP_STATUS = self.visual_grid_tooltip_status.isChecked()
		set(gui_constants.TOOLTIP_STATUS, 'Visual', 'tooltip status')
		gui_constants.TOOLTIP_TYPE = self.visual_grid_tooltip_type.isChecked()
		set(gui_constants.TOOLTIP_TYPE, 'Visual', 'tooltip type')
		gui_constants.TOOLTIP_LANG = self.visual_grid_tooltip_lang.isChecked()
		set(gui_constants.TOOLTIP_LANG, 'Visual', 'tooltip lang')
		gui_constants.TOOLTIP_DESCR = self.visual_grid_tooltip_descr.isChecked()
		set(gui_constants.TOOLTIP_DESCR, 'Visual', 'tooltip descr')
		gui_constants.TOOLTIP_TAGS = self.visual_grid_tooltip_tags.isChecked()
		set(gui_constants.TOOLTIP_TAGS, 'Visual', 'tooltip tags')
		gui_constants.TOOLTIP_LAST_READ = self.visual_grid_tooltip_last_read.isChecked()
		set(gui_constants.TOOLTIP_LAST_READ, 'Visual', 'tooltip last read')
		gui_constants.TOOLTIP_TIMES_READ = self.visual_grid_tooltip_times_read.isChecked()
		set(gui_constants.TOOLTIP_TIMES_READ, 'Visual', 'tooltip times read')
		gui_constants.TOOLTIP_PUB_DATE = self.visual_grid_tooltip_pub_date.isChecked()
		set(gui_constants.TOOLTIP_PUB_DATE, 'Visual', 'tooltip pub date')
		gui_constants.TOOLTIP_DATE_ADDED = self.visual_grid_tooltip_date_added.isChecked()
		set(gui_constants.TOOLTIP_DATE_ADDED, 'Visual', 'tooltip date added')
		
		# Advanced / Misc
		# grid view
		gui_constants.SCROLL_SPEED = self.scroll_speed
		set(self.scroll_speed, 'Advanced', 'scroll speed')
		self.scroll_speed_changed.emit()
		gui_constants.THUMBNAIL_CACHE_SIZE = self.cache_size
		set(self.cache_size[1], 'Advanced', 'cache size')
		QPixmapCache.setCacheLimit(self.cache_size[0]*
							 self.cache_size[1])
		# search
		gui_constants.ALLOW_SEARCH_REGEX = self.search_allow_regex.isChecked()
		set(gui_constants.ALLOW_SEARCH_REGEX, 'Advanced', 'allow search regex')
		gui_constants.SEARCH_AUTOCOMPLETE = self.search_autocomplete.isChecked()
		set(gui_constants.SEARCH_AUTOCOMPLETE, 'Advanced', 'search autocomplete')
		if self.search_on_enter.isChecked():
			gui_constants.SEARCH_ON_ENTER = True
		else:
			gui_constants.SEARCH_ON_ENTER = False
		set(gui_constants.SEARCH_ON_ENTER, 'Advanced', 'search on enter')

		settings.save()
		self.close()

	def init_right_panel(self):

		#def title_def(title):
		#	title_lbl = QLabel(title)
		#	f = QFont()
		#	f.setPixelSize(16)
		#	title_lbl.setFont(f)
		#	return title_lbl

		# Web
		web = QTabWidget()
		self.web_index = self.right_panel.addWidget(web)
		web_general_page = QWidget()
		web.addTab(web_general_page, 'General')
		web.setTabEnabled(0, False)
		exhentai_page = QWidget()
		web.addTab(exhentai_page, 'ExHentai')
		web.setCurrentIndex(1)
		ipb_layout = QFormLayout()
		exhentai_page.setLayout(ipb_layout)
		# exhentai
		self.ipbid_edit = QLineEdit()
		self.ipbpass_edit = QLineEdit()
		exh_tutorial = QLabel(gui_constants.EXHEN_COOKIE_TUTORIAL)
		exh_tutorial.setTextFormat(Qt.RichText)
		ipb_layout.addRow('IPB Member ID:', self.ipbid_edit)
		ipb_layout.addRow('IPB Pass Hash:', self.ipbpass_edit)
		ipb_layout.addRow(exh_tutorial)

		# Visual
		visual = QTabWidget()
		self.visual_index = self.right_panel.addWidget(visual)
		visual_general_page = QWidget()
		visual.addTab(visual_general_page, 'General')

		gallery_general_page = QWidget()
		visual.addTab(gallery_general_page, 'Gallery')
		gallery_layout = QVBoxLayout()
		gallery_general_page.setLayout(gallery_layout)
		# grid view
		grid_view_group = QGroupBox('Grid View')
		gallery_layout.addWidget(grid_view_group)
		grid_view_layout = QHBoxLayout()
		grid_view_group.setLayout(grid_view_layout)
		# grid view / tooltip
		self.grid_tooltip_group = QGroupBox('Tooltip', grid_view_group)
		self.grid_tooltip_group.setCheckable(True)
		grid_view_layout.addWidget(self.grid_tooltip_group)
		grid_tooltip_layout = QFormLayout()
		self.grid_tooltip_group.setLayout(grid_tooltip_layout)
		grid_tooltip_layout.addRow(QLabel('Control what is'+
									' displayed in the tooltip'))
		grid_tooltips_hlayout = FlowLayout()
		grid_tooltip_layout.addRow(grid_tooltips_hlayout)
		self.visual_grid_tooltip_title = QCheckBox('Title')
		grid_tooltips_hlayout.addWidget(self.visual_grid_tooltip_title)
		self.visual_grid_tooltip_author = QCheckBox('Author')
		grid_tooltips_hlayout.addWidget(self.visual_grid_tooltip_author)
		self.visual_grid_tooltip_chapters = QCheckBox('Chapters')
		grid_tooltips_hlayout.addWidget(self.visual_grid_tooltip_chapters)
		self.visual_grid_tooltip_status = QCheckBox('Status')
		grid_tooltips_hlayout.addWidget(self.visual_grid_tooltip_status)
		self.visual_grid_tooltip_type = QCheckBox('Type')
		grid_tooltips_hlayout.addWidget(self.visual_grid_tooltip_type)
		self.visual_grid_tooltip_lang = QCheckBox('Language')
		grid_tooltips_hlayout.addWidget(self.visual_grid_tooltip_type)
		self.visual_grid_tooltip_descr = QCheckBox('Description')
		grid_tooltips_hlayout.addWidget(self.visual_grid_tooltip_descr)
		self.visual_grid_tooltip_tags = QCheckBox('Tags')
		grid_tooltips_hlayout.addWidget(self.visual_grid_tooltip_tags)
		self.visual_grid_tooltip_last_read = QCheckBox('Last read')
		grid_tooltips_hlayout.addWidget(self.visual_grid_tooltip_last_read)
		self.visual_grid_tooltip_times_read = QCheckBox('Times read')
		grid_tooltips_hlayout.addWidget(self.visual_grid_tooltip_times_read)
		self.visual_grid_tooltip_pub_date = QCheckBox('Publication Date')
		grid_tooltips_hlayout.addWidget(self.visual_grid_tooltip_pub_date)
		self.visual_grid_tooltip_date_added = QCheckBox('Date added')
		grid_tooltips_hlayout.addWidget(self.visual_grid_tooltip_date_added)

		style_page = QWidget()
		visual.addTab(style_page, 'Style')
		visual.setTabEnabled(0, False)
		visual.setTabEnabled(2, False)
		visual.setCurrentIndex(1)

		# Advanced
		advanced = QTabWidget()
		self.advanced_index = self.right_panel.addWidget(advanced)
		advanced_misc = QWidget()
		advanced.addTab(advanced_misc, 'Misc')
		advanced_misc_main_layout = QVBoxLayout()
		advanced_misc.setLayout(advanced_misc_main_layout)
		misc_controls_layout = QFormLayout()
		misc_controls_layout.addWidget(QLabel('Options marked with * requires application restart'))
		advanced_misc_main_layout.addLayout(misc_controls_layout)
		# scroll speed
		misc_gridview = QGroupBox('Grid View')
		misc_controls_layout.addWidget(misc_gridview)
		misc_gridview_layout = QFormLayout()
		misc_gridview.setLayout(misc_gridview_layout)
		scroll_speed_spin_box = QSpinBox()
		scroll_speed_spin_box.setFixedWidth(60)
		scroll_speed_spin_box.setToolTip('Control the speed when scrolling in'+
								   ' grid view. DEFAULT: 7')
		scroll_speed_spin_box.setValue(self.scroll_speed)
		def scroll_speed(v): self.scroll_speed = v
		scroll_speed_spin_box.valueChanged[int].connect(scroll_speed)
		misc_gridview_layout.addRow('Scroll speed:', scroll_speed_spin_box)
		# cache size
		cache_size_spin_box = QSpinBox()
		cache_size_spin_box.setFixedWidth(120)
		cache_size_spin_box.setMaximum(999999999)
		cache_size_spin_box.setToolTip('This will greatly improve the grid view.' +
								 ' Increase the value if you experience lag when scrolling'+
								 ' through galleries. DEFAULT: 200 MiB')
		def cache_size(c): self.cache_size = (self.cache_size[0], c)
		cache_size_spin_box.setValue(self.cache_size[1])
		cache_size_spin_box.valueChanged[int].connect(cache_size)
		misc_gridview_layout.addRow('Cache Size (MiB):', cache_size_spin_box)		
		# regex
		misc_search = QGroupBox('Search')
		misc_controls_layout.addWidget(misc_search)
		misc_search_layout = QFormLayout()
		misc_search.setLayout(misc_search_layout)
		search_allow_regex_l = QHBoxLayout()
		self.search_allow_regex = QCheckBox()
		self.search_allow_regex.setChecked(gui_constants.ALLOW_SEARCH_REGEX)
		self.search_allow_regex.adjustSize()
		self.search_allow_regex.setToolTip('A regex tutorial is located in About->Regex Cheatsheet')
		search_allow_regex_l.addWidget(self.search_allow_regex)
		search_allow_regex_l.addWidget(QLabel('A regex tutorial is located in About->Regex Cheatsheet'))
		search_allow_regex_l.addWidget(Spacer('h'))
		misc_search_layout.addRow('Regex:', search_allow_regex_l)
		# autocomplete
		self.search_autocomplete = QCheckBox('*')
		self.search_autocomplete.setChecked(gui_constants.SEARCH_AUTOCOMPLETE)
		self.search_autocomplete.setToolTip('Turn autocomplete on/off')
		misc_search_layout.addRow('Autocomplete', self.search_autocomplete)
		# search behaviour
		self.search_every_keystroke = QRadioButton('Search on every keystroke *', misc_search)
		misc_search_layout.addRow(self.search_every_keystroke)
		self.search_on_enter = QRadioButton('Search on enter-key *', misc_search)
		misc_search_layout.addRow(self.search_on_enter)

		# Advanced / Database
		advanced_db_page = QWidget()
		advanced.addTab(advanced_db_page, 'Database')
		advanced.setTabEnabled(1, False)


		# About
		about = QTabWidget()
		self.about_index = self.right_panel.addWidget(about)
		about_happypanda_page = QWidget()
		about_troubleshoot_page = QWidget()
		about.addTab(about_happypanda_page, 'About Happypanda')
		about_layout = QVBoxLayout()
		about_happypanda_page.setLayout(about_layout)
		info_lbl = QLabel('<b>Author:</b> <a href=\'https://github.com/Pewpews\'>'+
					'Pewpews</a><br/>'+
					'Chat: <a href=\'https://gitter.im/Pewpews/happypanda\'>'+
					'Gitter chat</a><br/>'+
					'Email: happypandabugs@gmail.com<br/>'+
					'<b>Current version {}</b><br/>'.format(gui_constants.vs)+
					'Happypanda was created using:<br/>'+
					'- Python 3.4<br/>'+
					'- The Qt5 Framework')
		info_lbl.setOpenExternalLinks(True)
		about_layout.addWidget(info_lbl, 0, Qt.AlignTop)
		gpl_lbl = QLabel(gui_constants.GPL)
		gpl_lbl.setOpenExternalLinks(True)
		gpl_lbl.setWordWrap(True)
		about_layout.addWidget(gpl_lbl, 0, Qt.AlignTop)
		about_layout.addWidget(Spacer('v'))
		# About / Tags
		about_tags_page = QWidget()
		about.addTab(about_tags_page, 'Tags')
		about.setTabEnabled(1, False)
		# list of tags/namespaces here

		# About / Troubleshooting
		about.addTab(about_troubleshoot_page, 'Troubleshooting Guide')
		troubleshoot_layout = QVBoxLayout()
		about_troubleshoot_page.setLayout(troubleshoot_layout)
		guide_lbl = QLabel(gui_constants.TROUBLE_GUIDE)
		guide_lbl.setTextFormat(Qt.RichText)
		guide_lbl.setOpenExternalLinks(True)
		troubleshoot_layout.addWidget(guide_lbl, 0, Qt.AlignTop)
		troubleshoot_layout.addWidget(Spacer('v'))
		# About / Search tutorial
		about_search_tut = QWidget()
		about.addTab(about_search_tut, 'Regex Cheatsheet')
		about_search_tut_l = QVBoxLayout()
		about_search_tut.setLayout(about_search_tut_l)
		# tags

		# regex
		about_s_regex = QGroupBox('Regex')
		about_search_tut_l.addWidget(about_s_regex)
		about_s_regex_l = QFormLayout()
		about_s_regex.setLayout(about_s_regex_l)
		about_s_regex_l.addRow('\\\\\\\\', QLabel('Match literally \\'))
		about_s_regex_l.addRow('.', QLabel('Match any single character'))
		about_s_regex_l.addRow('^', QLabel('Start of string'))
		about_s_regex_l.addRow('$', QLabel('End of string'))
		about_s_regex_l.addRow('\\d', QLabel('Match any decimal digit'))
		about_s_regex_l.addRow('\\D', QLabel('Match any non-digit character'))
		about_s_regex_l.addRow('\\s', QLabel('Match any whitespace character'))
		about_s_regex_l.addRow('\\S', QLabel('Match any non-whitespace character'))
		about_s_regex_l.addRow('\\w', QLabel('Match any alphanumeric character'))
		about_s_regex_l.addRow('\\W', QLabel('Match any non-alphanumeric character'))
		about_s_regex_l.addRow('*', QLabel('Repeat previous character zero or more times'))
		about_s_regex_l.addRow('+', QLabel('Repeat previous character one or more times'))
		about_s_regex_l.addRow('?', QLabel('Repeat previous character one or zero times'))
		about_s_regex_l.addRow('{m, n}', QLabel('Repeat previous character atleast <i>m</i> times but no more than <i>n</i> times'))
		about_s_regex_l.addRow('(...)', QLabel('Match everything enclosed'))
		about_s_regex_l.addRow('(a|b)', QLabel('Match either a or b'))
		about_s_regex_l.addRow('[abc]', QLabel('Match a single character of: a, b or c'))
		about_s_regex_l.addRow('[^abc]', QLabel('Match a character except: a, b or c'))
		about_s_regex_l.addRow('[a-z]', QLabel('Match a character in the range'))
		about_s_regex_l.addRow('[^a-z]', QLabel('Match a character not in the range'))


	def reject(self):
		self.close()

class PathLineEdit(QLineEdit):
	def __init(self, parent=None, dir=True):
		super().__init__(parent)
		self.folder = dir

	def openExplorer(self):
		if self.folder:
			path = QFileDialog.getExistingDirectory(self,
										   'Choose folder')
		else:
			path = QFileDialog.getOpenFileName(self,
									  'Choose file')
			path = path[0]
		if len(path) != 0:
			self.setText(path)

	def mousePressEvent(self, event):
		assert isinstance(event, QMouseEvent)
		if len(self.text()) == 0:
			if event.button() == Qt.LeftButton:
				self.openExplorer()
			else:
				return super().mousePressEvent(event)
		if event.button() == Qt.RightButton:
			self.openExplorer()
			
		super().mousePressEvent(event)

class ChapterAddWidget(QWidget):
	CHAPTERS = pyqtSignal(dict)
	def __init__(self, gallery, parent=None):
		super().__init__(parent)
		self.setWindowFlags(Qt.Window)

		self.current_chapters = len(gallery.chapters)
		self.added_chaps = 0

		layout = QFormLayout()
		self.setLayout(layout)
		lbl = QLabel('[{} {}]'.format(gallery.artist, gallery.title))
		layout.addRow('Gallery:', lbl)
		layout.addRow('Current chapters:', QLabel('{}'.format(self.current_chapters)))

		new_btn = QPushButton('New')
		new_btn.clicked.connect(self.add_new_chapter)
		new_btn.adjustSize()
		add_btn = QPushButton('Finish')
		add_btn.clicked.connect(self.finish)
		add_btn.adjustSize()
		new_l = QHBoxLayout()
		new_l.addWidget(add_btn, alignment=Qt.AlignLeft)
		new_l.addWidget(new_btn, alignment=Qt.AlignRight)
		layout.addRow(new_l)

		frame = QFrame()
		frame.setFrameShape(frame.StyledPanel)
		layout.addRow(frame)

		self.chapter_l = QVBoxLayout()
		frame.setLayout(self.chapter_l)

		new_btn.click()

		self.setMaximumHeight(550)
		self.setFixedWidth(500)
		if parent:
			self.move(parent.window().frameGeometry().topLeft() +
				parent.window().rect().center() -
				self.rect().center())
		else:
			frect = self.frameGeometry()
			frect.moveCenter(QDesktopWidget().availableGeometry().center())
			self.move(frect.topLeft())
		self.setWindowTitle('Add Chapters')

	def add_new_chapter(self):
		chap_layout = QHBoxLayout()
		self.added_chaps += 1
		curr_chap = self.current_chapters+self.added_chaps

		chp_numb = QSpinBox(self)
		chp_numb.setMinimum(1)
		chp_numb.setValue(curr_chap)
		curr_chap_lbl = QLabel('Chapter {}'.format(curr_chap))
		def ch_lbl(n): curr_chap_lbl.setText('Chapter {}'.format(n))
		chp_numb.valueChanged[int].connect(ch_lbl)
		chp_path = PathLineEdit()
		chp_path.folder = True
		chp_path.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
		chp_path.setPlaceholderText('Right/Left-click to open folder explorer.'+
							  ' Leave empty to not add.')
		chap_layout.addWidget(chp_path, 3)
		chap_layout.addWidget(chp_numb, 0)
		self.chapter_l.addWidget(curr_chap_lbl,
						   alignment=Qt.AlignLeft)
		self.chapter_l.addLayout(chap_layout)

	def finish(self):
		chapters = {}
		widgets = []
		x = True
		while x:
			x = self.chapter_l.takeAt(0)
			if x:
				widgets.append(x)
		for l in range(1, len(widgets), 1):
			layout = widgets[l]
			try:
				line_edit = layout.itemAt(0).widget()
				spin_box = layout.itemAt(1).widget()
			except AttributeError:
				continue
			p = line_edit.text()
			c = spin_box.value() - 1 # because of 0-based index
			if os.path.exists(p):
				chapters[c] = p
		self.CHAPTERS.emit(chapters)
		self.close()


class GalleryListItem(QListWidgetItem):
	def __init__(self, gallery=None, parent=None):
		super().__init__(parent)
		self.gallery = gallery


class GalleryListView(QWidget):
	SERIES = pyqtSignal(list)
	def __init__(self, parent=None, modal=False):
		super().__init__(parent)
		self.setWindowFlags(Qt.Dialog)

		layout = QVBoxLayout()
		self.setLayout(layout)

		if modal:
			frame = QFrame()
			frame.setFrameShape(frame.StyledPanel)
			modal_layout = QHBoxLayout()
			frame.setLayout(modal_layout)
			layout.addWidget(frame)
			info = QLabel('This mode let\'s you add galleries from ' +
				 'different folders.')
			f_folder = QPushButton('Add folders')
			f_folder.clicked.connect(self.from_folder)
			f_files = QPushButton('Add files')
			f_files.clicked.connect(self.from_files)
			modal_layout.addWidget(info, 3, Qt.AlignLeft)
			modal_layout.addWidget(f_folder, 0, Qt.AlignRight)
			modal_layout.addWidget(f_files, 0, Qt.AlignRight)

		check_layout = QHBoxLayout()
		layout.addLayout(check_layout)
		if modal:
			check_layout.addWidget(QLabel('Please uncheck galleries you do' +
							  ' not want to add. (Exisiting galleries won\'t be added'),
							 3)
		else:
			check_layout.addWidget(QLabel('Please uncheck galleries you do' +
							  ' not want to add. (Existing galleries are hidden)'),
							 3)
		self.check_all = QCheckBox('Check/Uncheck All', self)
		self.check_all.setChecked(True)
		self.check_all.stateChanged.connect(self.all_check_state)

		check_layout.addWidget(self.check_all)
		self.view_list = QListWidget()
		self.view_list.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOn)
		self.view_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
		layout.addWidget(self.view_list)
		
		add_btn = QPushButton('Add checked')
		add_btn.clicked.connect(self.return_gallery)

		cancel_btn = QPushButton('Cancel')
		cancel_btn.clicked.connect(self.close_window)
		btn_layout = QHBoxLayout()

		spacer = QWidget()
		spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
		btn_layout.addWidget(spacer)
		btn_layout.addWidget(add_btn)
		btn_layout.addWidget(cancel_btn)
		layout.addLayout(btn_layout)

		self.resize(500,550)
		frect = self.frameGeometry()
		frect.moveCenter(QDesktopWidget().availableGeometry().center())
		self.move(frect.topLeft())
		self.setWindowTitle('Gallery List')

	def all_check_state(self, new_state):
		row = 0
		done = False
		while not done:
			item = self.view_list.item(row)
			if item:
				row += 1
				if new_state == Qt.Unchecked:
					item.setCheckState(Qt.Unchecked)
				else:
					item.setCheckState(Qt.Checked)
			else:
				done = True

	def add_gallery(self, item, name):
		"""
		Constructs an widgetitem to hold the provided item,
		and adds it to the view_list
		"""
		assert isinstance(name, str)
		gallery_item = GalleryListItem(item)
		gallery_item.setText(name)
		gallery_item.setFlags(gallery_item.flags() | Qt.ItemIsUserCheckable)
		gallery_item.setCheckState(Qt.Checked)
		self.view_list.addItem(gallery_item)

	def return_gallery(self):
		gallery_list = []
		row = 0
		done = False
		while not done:
			item = self.view_list.item(row)
			if not item:
				done = True
			else:
				if item.checkState() == Qt.Checked:
					gallery_list.append(item.gallery)
				row += 1

		self.SERIES.emit(gallery_list)
		self.close()

	def from_folder(self):
		file_dialog = QFileDialog()
		file_dialog.setFileMode(QFileDialog.DirectoryOnly)
		file_dialog.setOption(QFileDialog.DontUseNativeDialog, True)
		file_view = file_dialog.findChild(QListView, 'listView')
		if file_view:
			file_view.setSelectionMode(QAbstractItemView.MultiSelection)
		f_tree_view = file_dialog.findChild(QTreeView)
		if f_tree_view:
			f_tree_view.setSelectionMode(QAbstractItemView.MultiSelection)

		if file_dialog.exec():
			for path in file_dialog.selectedFiles():
				self.add_gallery(path, os.path.split(path)[1])


	def from_files(self):
		gallery_list = QFileDialog.getOpenFileNames(self,
											 'Select 1 or more gallery to add',
											 filter='Archives (*.zip *.cbz)')
		for path in gallery_list[0]:
			#Warning: will break when you add more filters
			if len(path) != 0:
				self.add_gallery(path, os.path.split(path)[1])

	def close_window(self):
		msgbox = QMessageBox()
		msgbox.setText('Are you sure you want to cancel?')
		msgbox.setStandardButtons(msgbox.Yes | msgbox.No)
		msgbox.setDefaultButton(msgbox.No)
		msgbox.setIcon(msgbox.Question)
		if msgbox.exec() == QMessageBox.Yes:
			self.close()

class Loading(QWidget):
	ON = False #to prevent multiple instances
	def __init__(self, parent=None):
		super().__init__(parent)
		self.widget = QWidget(self)
		self.widget.setStyleSheet("background-color:rgba(0, 0, 0, 0.65)")
		self.progress = QProgressBar()
		self.progress.setStyleSheet("color:white")
		self.text = QLabel()
		self.text.setAlignment(Qt.AlignCenter)
		self.text.setStyleSheet("color:white;background-color:transparent;")
		layout_ = QHBoxLayout()
		inner_layout_ = QVBoxLayout()
		inner_layout_.addWidget(self.text, 0, Qt.AlignHCenter)
		inner_layout_.addWidget(self.progress)
		self.widget.setLayout(inner_layout_)
		layout_.addWidget(self.widget)
		self.setLayout(layout_)
		self.resize(300,100)
		#frect = self.frameGeometry()
		#frect.moveCenter(QDesktopWidget().availableGeometry().center())
		self.move(parent.window().frameGeometry().topLeft() +
			parent.window().rect().center() -
			self.rect().center() - QPoint(self.rect().width()//2,0))
		#self.setAttribute(Qt.WA_DeleteOnClose)
		#self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint)

	def mousePressEvent(self, QMouseEvent):
		pass

	def setText(self, string):
		if string != self.text.text():
			self.text.setText(string)

class CompleterTextEdit(QTextEdit):
	"""
	A textedit with autocomplete
	"""
	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.completer = None
		log_d('Instantiat CompleterTextEdit: OK')

	def setCompleter(self, completer):
		if self.completer:
			self.disconnect(self.completer, 0, self, 0)
		if not completer:
			return None

		completer.setWidget(self)
		completer.setCompletionMode(QCompleter.PopupCompletion)
		completer.setCaseSensitivity(Qt.CaseInsensitive)
		self.completer = completer
		self.completer.insertText.connect(self.insertCompletion)

	def insertCompletion(self, completion):
		tc = self.textCursor()
		extra = (len(completion) -
		   len(self.completer.completionPrefix()))
		tc.movePosition(QTextCursor.Left)
		tc.movePosition(QTextCursor.EndOfWord)
		tc.insertText(completion[-extra:])
		self.setTextCursor(tc)

	def textUnderCursor(self):
		tc = self.textCursor()
		tc.select(QTextCursor.WordUnderCursor)
		return tc.selectedText()

	def focusInEvent(self, event):
		if self.completer:
			self.completer.setWidget(self)
		super().focusInEvent(event)

	def keyPressEvent(self, event):
		if self.completer and self.completer.popup() and \
			self.completer.popup().isVisible():
			if event.key() in (
				Qt.Key_Enter,
				Qt.Key_Return,
				Qt.Key_Tab,
				Qt.Key_Escape,
				Qt.Key_Backtab):
				event.ignore()
				return None

		# to show popup shortcut
		isShortcut = event.modifiers() == Qt.ControlModifier and \
			    event.key() == Qt.Key_Space

		# to complete suggestion inline
		inline = event.key() == Qt.Key_Tab

		if inline:
			self.completer.setCompletionMode(QCompleter.InlineCompletion)
			completionPrefix = self.textUnderCursor()
			if completionPrefix != self.completer.completionPrefix():
				self.completer.setCompletionPrefix(completionPrefix)
			self.completer.complete()

			# set the current suggestion in text box
			self.completer.insertText.emit(self.completer.currentCompletion())
			#reset completion mode
			self.completer.setCompletionMode(QCompleter.PopupCompletion)
			return None
		if not self.completer or not isShortcut:
			super().keyPressEvent(event)
		
		ctrlOrShift = event.modifiers() in (Qt.ControlModifier,
									  Qt.ShiftModifier)
		if ctrlOrShift and event.text() == '':
			return None

		#end of word
		eow = "~!@#$%^&*+{}|:\"<>?,./;'[]\\-="
		
		hasModifier = event.modifiers() != Qt.NoModifier and not ctrlOrShift
		completionPrefix = self.textUnderCursor()

		if not isShortcut:
			if self.completer.popup():
				self.completer.popup().hide()
			return None

		self.completer.setCompletionPrefix(completionPrefix)
		popup = self.completer.popup()
		popup.setCurrentIndex(self.completer.completionModel().index(0,0))
		cr = self.cursorRect()
		cr.setWidth(self.completer.popup().sizeHintForColumn(0) +
			  self.completer.popup().verticalScrollBar().sizeHint().width())
		self.completer.complete(cr)

class CompleterWithData(QCompleter):
	"""
	Instantiate a QCompleter with predefined data
	"""
	insertText = pyqtSignal(str)

	def __init__(self, data, parent=None):
		assert isinstance(data, list)
		super().__init__(data, parent)
		self.activated[str].connect(self.changeCompletion)
		log_d('Instantiate CompleterWithData: OK')

	def changeCompletion(self, completion):
		if completion.find('(') != -1:
			completion = completion[:completion.find('(')]
		#print(completion)
		self.insertText.emit(completion)



def return_tag_completer_TextEdit():
	ns = gallerydb.TagDB.get_all_ns()
	for t in gallerydb.TagDB.get_all_tags():
		ns.append(t)
	TextEditCompleter = CompleterTextEdit()
	TextEditCompleter.setCompleter(CompleterWithData(ns))
	return TextEditCompleter

from PyQt5.QtCore import QSortFilterProxyModel
class DatabaseFilterProxyModel(QSortFilterProxyModel):
	"""
	A proxy model to hide items already in database
	Pass a tuple with entries to 'filters' param if you need a custom filter.
	"""
	def __init__(self, filters="", parent=None):
		super().__init__(parent)
		self.filters = tuple(filters)
		self.role = Qt.DisplayRole
		db_data = gallerydb.GalleryDB.get_all_gallery()
		filter_list = []
		for gallery in db_data:
			p = os.path.split(gallery.path)
			filter_list.append(p[1])
		self.filter_list = sorted(filter_list)
		#print('Instatiated')

	def set_name_role(self, role):
		self.role = role
		self.invalidateFilter()

	def filterAcceptsRow(self, source_row, index_parent):
		#print('Using')
		allow = False
		index = self.sourceModel().index(source_row, 0, index_parent)

		if self.sourceModel() and index.isValid():
			allow = True
			name = index.data(self.role)
			if name.endswith(self.filters):
				if binary_search(name):
					#print('Hiding {}'.format(name))
					allow = True
		return allow

class GalleryDialog(QWidget):
	"A window for adding/modifying gallery"

	gallery_queue = queue.Queue()
	SERIES = pyqtSignal(list)
	SERIES_EDIT = pyqtSignal(list, int)
	#gallery_list = [] # might want to extend this to allow mass gallery adding

	def __init__(self, parent=None, list_of_index=None):
		super().__init__(parent, Qt.Dialog)
		log_d('Triggered Gallery Edit/Add Dialog')
		self.main_layout = QVBoxLayout()

		if not list_of_index:
			self.newUI()
			self.commonUI()
			self.done.clicked.connect(self.accept)
			self.cancel.clicked.connect(self.reject)
		else:
			assert isinstance(list_of_index, list)
			self.position = list_of_index[0].row()
			for index in list_of_index:
				gallery = index.data(Qt.UserRole+1)
				self.commonUI()
				self.setGallery(gallery)

			self.done.clicked.connect(self.accept_edit)
			self.cancel.clicked.connect(self.reject_edit)

		log_d('GalleryDialog: Create UI: successful')
		#TODO: Implement a way to mass add galleries
		#IDEA: Extend dialog in a ScrollArea with more forms...

		self.setLayout(self.main_layout)
		self.resize(500,200)
		frect = self.frameGeometry()
		frect.moveCenter(QDesktopWidget().availableGeometry().center())
		self.move(frect.topLeft()-QPoint(0,180))
		#self.setAttribute(Qt.WA_DeleteOnClose)
		self.setWindowTitle("Add a new gallery")

	def commonUI(self):
		f_web = QGroupBox("Metadata from the Web")
		f_web.setCheckable(False)
		self.main_layout.addWidget(f_web)
		web_main_layout = QVBoxLayout()
		web_layout = QHBoxLayout()
		web_main_layout.addLayout(web_layout)
		f_web.setLayout(web_main_layout)

		f_gallery = QGroupBox("Gallery Info")
		f_gallery.setCheckable(False)
		self.main_layout.addWidget(f_gallery)
		gallery_layout = QFormLayout()
		f_gallery.setLayout(gallery_layout)

		def basic_web(name):
			return QLabel(name), QLineEdit(), QPushButton("Fetch"), QProgressBar()

		url_lbl, self.url_edit, url_btn, url_prog = basic_web("URL:")
		url_btn.clicked.connect(lambda: self.web_metadata(self.url_edit.text(), url_btn,
											url_prog))
		url_prog.setTextVisible(False)
		url_prog.setMinimum(0)
		url_prog.setMaximum(0)
		web_layout.addWidget(url_lbl, 0, Qt.AlignLeft)
		web_layout.addWidget(self.url_edit, 0)
		web_layout.addWidget(url_btn, 0, Qt.AlignRight)
		web_layout.addWidget(url_prog, 0, Qt.AlignRight)
		self.url_edit.setPlaceholderText("paste g.e-hentai/exhentai gallery link")
		url_prog.hide()

		self.title_edit = QLineEdit()
		self.author_edit = QLineEdit()
		self.descr_edit = QTextEdit()
		self.descr_edit.setFixedHeight(45)
		self.descr_edit.setAcceptRichText(True)
		self.descr_edit.setPlaceholderText("HTML 4 tags are supported")
		self.lang_box = QComboBox()
		self.lang_box.addItems(["English", "Japanese", "Other"])
		self.lang_box.setCurrentIndex(0)
		self.tags_edit = return_tag_completer_TextEdit()
		self.tags_edit.setFixedHeight(70)
		self.tags_edit.setPlaceholderText("Autocomplete enabled. Press Tab (Ctrl + Space to show popup)"+
									"\nnamespace1:tag1, tag2, namespace3:tag3, etc..")
		self.type_box = QComboBox()
		self.type_box.addItems(["Manga", "Doujinshi", "Artist CG Sets", "Game CG Sets",
						  "Western", "Image Sets", "Non-H", "Cosplay", "Other"])
		self.type_box.setCurrentIndex(0)
		#self.type_box.currentIndexChanged[int].connect(self.doujin_show)
		#self.doujin_parent = QLineEdit()
		#self.doujin_parent.setVisible(False)
		self.status_box = QComboBox()
		self.status_box.addItems(["Unknown", "Ongoing", "Completed"])
		self.status_box.setCurrentIndex(0)
		self.pub_edit = QDateEdit()
		self.pub_edit.setCalendarPopup(True)
		self.pub_edit.setDate(QDate.currentDate())
		self.path_lbl = QLabel("")
		self.path_lbl.setWordWrap(True)

		link_layout = QHBoxLayout()
		self.link_lbl = QLabel("")
		self.link_lbl.setWordWrap(True)
		self.link_edit = QLineEdit()
		link_layout.addWidget(self.link_edit)
		link_layout.addWidget(self.link_lbl)
		self.link_edit.hide()
		self.link_btn = QPushButton("Modify")
		self.link_btn.setFixedWidth(50)
		self.link_btn2 = QPushButton("Set")
		self.link_btn2.setFixedWidth(40)
		self.link_btn.clicked.connect(self.link_modify)
		self.link_btn2.clicked.connect(self.link_set)
		link_layout.addWidget(self.link_btn)
		link_layout.addWidget(self.link_btn2)
		self.link_btn2.hide()

		gallery_layout.addRow("Title:", self.title_edit)
		gallery_layout.addRow("Author:", self.author_edit)
		gallery_layout.addRow("Description:", self.descr_edit)
		gallery_layout.addRow("Language:", self.lang_box)
		gallery_layout.addRow("Tags:", self.tags_edit)
		gallery_layout.addRow("Type:", self.type_box)
		gallery_layout.addRow("Publication Date:", self.pub_edit)
		gallery_layout.addRow("Path:", self.path_lbl)
		gallery_layout.addRow("Link:", link_layout)

		final_buttons = QHBoxLayout()
		final_buttons.setAlignment(Qt.AlignRight)
		self.main_layout.addLayout(final_buttons)
		self.done = QPushButton("Done")
		self.done.setDefault(True)
		self.cancel = QPushButton("Cancel")
		final_buttons.addWidget(self.cancel)
		final_buttons.addWidget(self.done)

		self.title_edit.setFocus()

	def setGallery(self, gallery):
		"To be used for when editing a gallery"
		self.gallery = gallery

		self.url_edit.setText(gallery.link)

		self.title_edit.setText(gallery.title)
		self.author_edit.setText(gallery.artist)
		self.descr_edit.setText(gallery.info)

		if gallery.language.lower() in "english":
			self.lang_box.setCurrentIndex(0)
		elif gallery.language.lower() in "japanese":
			self.lang_box.setCurrentIndex(1)
		else:
			self.lang_box.setCurrentIndex(2)

		self.tags_edit.setText(tag_to_string(gallery.tags))

		t_index = self.type_box.findText(gallery.type)
		try:
			self.type_box.setCurrentIndex(t_index)
		except:
			self.type_box.setCurrentIndex(0)

		if gallery.status is "Ongoing":
			self.status_box.setCurrentIndex(1)
		elif gallery.status is "Completed":
			self.status_box.setCurrentIndex(2)
		else:
			self.status_box.setCurrentIndex(0)

		gallery_pub_date = "{}".format(gallery.pub_date)
		qdate_pub_date = QDate.fromString(gallery_pub_date, "yyyy-MM-dd")
		self.pub_edit.setDate(qdate_pub_date)

		self.link_lbl.setText(gallery.link)
		self.path_lbl.setText(gallery.path)

	def newUI(self):

		f_local = QGroupBox("Folder/ZIP")
		f_local.setCheckable(False)
		self.main_layout.addWidget(f_local)
		local_layout = QHBoxLayout()
		f_local.setLayout(local_layout)

		choose_folder = QPushButton("From Folder")
		choose_folder.clicked.connect(lambda: self.choose_dir('f'))
		local_layout.addWidget(choose_folder)

		choose_archive = QPushButton("From ZIP")
		choose_archive.clicked.connect(lambda: self.choose_dir('a'))
		local_layout.addWidget(choose_archive)

		self.file_exists_lbl = QLabel()
		local_layout.addWidget(self.file_exists_lbl)
		self.file_exists_lbl.hide()

	def choose_dir(self, mode):
		if mode == 'a':
			name = QFileDialog.getOpenFileName(self, 'Choose archive',
											  filter='*.zip *.cbz')
			name = name[0]
		else:
			name = QFileDialog.getExistingDirectory(self, 'Choose folder')
		head, tail = os.path.split(name)
		parsed = title_parser(tail)
		self.title_edit.setText(parsed['title'])
		self.author_edit.setText(parsed['artist'])
		self.path_lbl.setText(name)
		l_i = self.lang_box.findText(parsed['language'])
		if l_i != -1:
			self.lang_box.setCurrentIndex(l_i)

		if gallerydb.GalleryDB.check_exists(tail):
			self.file_exists_lbl.setText('<font color="red">gallery already exists</font>')
			self.file_exists_lbl.show()
		else: self.file_exists_lbl.hide()

	def check(self):
		if len(self.title_edit.text()) is 0:
			self.title_edit.setFocus()
			self.title_edit.setStyleSheet("border-style:outset;border-width:2px;border-color:red;")
			return False
		elif len(self.author_edit.text()) is 0:
			self.author_edit.setText("Anon")

		if len(self.descr_edit.toPlainText()) is 0:
			self.descr_edit.setText("<i>No description..</i>")

		if len(self.path_lbl.text()) == 0 or self.path_lbl.text() == 'No path specified':
			self.path_lbl.setStyleSheet("color:red")
			self.path_lbl.setText('No path specified')
			return False

		return True

	def accept(self):

		def do_chapters(gallery):
			log_d('Starting chapters')
			thread = threading.Thread(target=self.set_chapters, args=(gallery,), daemon=True)
			thread.start()
			thread.join()
			log_d('Finished chapters')
			#return self.gallery_queue.get()

		if self.check():
			new_gallery = gallerydb.Gallery()
			new_gallery.title = self.title_edit.text()
			log_d('Adding gallery title')
			new_gallery.artist = self.author_edit.text()
			log_d('Adding gallery artist')
			new_gallery.path = self.path_lbl.text()
			log_d('Adding gallery path')
			new_gallery.info = self.descr_edit.toPlainText()
			log_d('Adding gallery descr')
			new_gallery.type = self.type_box.currentText()
			log_d('Adding gallery type')
			new_gallery.language = self.lang_box.currentText()
			log_d('Adding gallery lang')
			new_gallery.status = self.status_box.currentText()
			log_d('Adding gallery status')
			new_gallery.tags = tag_to_dict(self.tags_edit.toPlainText())
			log_d('Adding gallery: tagging to dict')
			qpub_d = self.pub_edit.date().toString("ddMMyyyy")
			dpub_d = datetime.strptime(qpub_d, "%d%m%Y").date()
			new_gallery.pub_date = dpub_d
			log_d('Adding gallery pub date')
			new_gallery.link = self.link_lbl.text()
			log_d('Adding gallery link')

			if self.path_lbl.text() == "unspecified...":
				self.SERIES.emit([new_gallery])
			else:
				updated_gallery = do_chapters(new_gallery)
				#for ser in self.gallery:
				#self.SERIES.emit([updated_gallery])
			self.close()

	def set_chapters(self, gallery_object):
		path = gallery_object.path
		try:
			log_d('Listing dir...')
			con = os.listdir(path) # list all folders in gallery dir
			log_d('Sorting')
			chapters = sorted([os.path.join(path,sub) for sub in con if os.path.isdir(os.path.join(path, sub))]) #subfolders
			# if gallery has chapters divided into sub folders
			if len(chapters) != 0:
				log_d('Chapters divided in folders..')
				for numb, ch in enumerate(chapters):
					chap_path = os.path.join(path, ch)
					gallery_object.chapters[numb] = chap_path

			else: #else assume that all images are in gallery folder
				gallery_object.chapters[0] = path
			log_d('Added chapters to gallery')
				
			#find last edited file
			times = set()
			log_d('Finding last update...')
			for root, dirs, files in os.walk(path, topdown=False):
				for img in files:
					fp = os.path.join(root, img)
					times.add(os.path.getmtime(fp))
			gallery_object.last_update = time.asctime(time.gmtime(max(times)))
			log_d('Found last update')
		except NotADirectoryError:
			if path[-4:] in ARCHIVE_FILES:
				log_d('Found an archive')
				#TODO: add support for folders in archive
				gallery_object.chapters[0] = path

		#self.gallery_queue.put(gallery_object)
		self.SERIES.emit([gallery_object])
		log_d('Sent gallery to model')
		#gallerydb.GalleryDB.add_gallery(gallery_object)
		

	def reject(self):
		if self.check():
			msgbox = QMessageBox()
			msgbox.setText("<font color='red'><b>Noo oniichan! You were about to add a new gallery.</b></font>")
			msgbox.setInformativeText("Do you really want to discard?")
			msgbox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
			msgbox.setDefaultButton(QMessageBox.No)
			if msgbox.exec() == QMessageBox.Yes:
				self.close()
		else:
			self.close()

	def web_metadata(self, url, btn_widget, pgr_widget):
		try:
			assert len(url) > 5
		except AssertionError:
			log_w('Invalid URL')
			return None
		self.link_lbl.setText(url)
		f = fetch.Fetch()
		f.web_url = url
		thread = QThread()

		def status(stat):
			def do_hide():
				try:
					pgr_widget.hide()
					btn_widget.show()
				except RuntimeError:
					pass

			if stat:
				do_hide()
			else:
				danger = """QProgressBar::chunk {
					background: QLinearGradient( x1: 0, y1: 0, x2: 1, y2: 0,stop: 0 #FF0350,stop: 0.4999 #FF0020,stop: 0.5 #FF0019,stop: 1 #FF0000 );
					border-bottom-right-radius: 5px;
					border-bottom-left-radius: 5px;
					border: .px solid black;}"""
				pgr_widget.setStyleSheet(danger)
				QTimer.singleShot(3000, do_hide)

		def t_del_later():
			thread.deleteLater
			thread.quit()

		f.moveToThread(thread)
		f.WEB_METADATA.connect(self.set_web_metadata)
		f.WEB_PROGRESS.connect(btn_widget.hide)
		f.WEB_PROGRESS.connect(pgr_widget.show)
		thread.started.connect(f.web)
		f.WEB_STATUS.connect(status)
		f.WEB_STATUS.connect(lambda: f.deleteLater)
		f.WEB_STATUS.connect(lambda: thread.deleteLater)
		thread.start()

	def set_web_metadata(self, metadata):
		assert isinstance(metadata, list)
		for gallery in metadata:
			parsed = title_parser(gallery['title'])
			self.title_edit.setText(parsed['title'])
			self.author_edit.setText(parsed['artist'])
			tags = ""
			lang = ['English', 'Japanese']
			l_i = self.lang_box.findText(parsed['language'])
			if l_i != -1:
				self.lang_box.setCurrentIndex(l_i)
			for n, tag in enumerate(gallery['tags'], 1):
				l_tag = tag.capitalize()
				if l_tag in lang:
					l_index = self.lang_box.findText(l_tag)
					if l_index != -1:
						self.lang_box.setCurrentIndex(l_index)
				else:
					if n == len(gallery['tags']):
						tags += tag
					else:
						tags += tag + ', '
			self.tags_edit.setText(tags)
			pub_dt = datetime.fromtimestamp(int(gallery['posted']))
			pub_string = "{}".format(pub_dt)
			pub_date = QDate.fromString(pub_string.split()[0], "yyyy-MM-dd")
			self.pub_edit.setDate(pub_date)
			t_index = self.type_box.findText(gallery['category'])
			try:
				self.type_box.setCurrentIndex(t_index)
			except:
				self.type_box.setCurrentIndex(0)


	def link_set(self):
		t = self.link_edit.text()
		self.link_edit.hide()
		self.link_lbl.show()
		self.link_lbl.setText(t)
		self.link_btn2.hide()
		self.link_btn.show() 

	def link_modify(self):
		t = self.link_lbl.text()
		self.link_lbl.hide()
		self.link_edit.show()
		self.link_edit.setText(t)
		self.link_btn.hide()
		self.link_btn2.show()

	def accept_edit(self):

		if self.check():
			new_gallery = self.gallery
			new_gallery.title = self.title_edit.text()
			new_gallery.artist = self.author_edit.text()
			new_gallery.path = self.path_lbl.text()
			new_gallery.info = self.descr_edit.toPlainText()
			new_gallery.type = self.type_box.currentText()
			new_gallery.language = self.lang_box.currentText()
			new_gallery.status = self.status_box.currentText()
			new_gallery.tags = tag_to_dict(self.tags_edit.toPlainText())
			qpub_d = self.pub_edit.date().toString("ddMMyyyy")
			dpub_d = datetime.strptime(qpub_d, "%d%m%Y").date()
			new_gallery.pub_date = dpub_d
			new_gallery.link = self.link_lbl.text()

			#for ser in self.gallery:
			self.SERIES_EDIT.emit([new_gallery], self.position)
			self.close()

	def reject_edit(self):
		self.close()