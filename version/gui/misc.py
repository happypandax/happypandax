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
						  QTimer, QObject, QSize, QRect, QFileInfo,
						  QMargins)
from PyQt5.QtGui import (QTextCursor, QIcon, QMouseEvent, QFont,
						 QPixmapCache, QPalette, QPainter, QBrush,
						 QColor, QPen, QPixmap)
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
							 QRadioButton, QFileIconProvider, QFontDialog,
							 QColorDialog, QScrollArea)

import os, threading, queue, time, logging, math, random
from datetime import datetime
from . import gui_constants
from ..utils import (tag_to_string, tag_to_dict, title_parser, ARCHIVE_FILES,
					 ArchiveFile, IMG_FILES, CreateZipFail)
from ..database import gallerydb, fetch, db
from .. import settings

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical

class BasePopup(QWidget):
	def __init__(self, parent=None, **kwargs):
		if kwargs:
			super().__init__(parent, **kwargs)
		else:
			super().__init__(parent, flags= Qt.Window | Qt.FramelessWindowHint)
		self.setAttribute(Qt.WA_TranslucentBackground)
		main_layout = QVBoxLayout()
		self.main_widget = QFrame()
		self.setLayout(main_layout)
		main_layout.addWidget(self.main_widget)
		self.generic_buttons = QHBoxLayout()
		self.generic_buttons.addWidget(Spacer('h'))
		self.yes_button = QPushButton('Yes')
		self.no_button = QPushButton('No')
		self.buttons_layout = QHBoxLayout()
		self.buttons_layout.addWidget(Spacer('h'), 3)
		self.generic_buttons.addWidget(self.yes_button)
		self.generic_buttons.addWidget(self.no_button)
		self.setMaximumWidth(500)
		self.resize(500,350)

	def add_buttons(self, *args):
		"""
		Pass names of buttons, from right to left.
		Returns list of buttons in same order.
		"""
		b = []
		for name in args:
			button = QPushButton(name)
			self.buttons_layout.addWidget(button)
			b.append(button)
		return b


class NotificationOverlay(QWidget):
	"""
	A notifaction bar
	"""
	clicked = pyqtSignal()
	def __init__(self, parent=None):
		super().__init__(parent)
		self._main_layout = QHBoxLayout(self)
		self._default_height = 20
		self._lbl = QLabel()
		self._main_layout.addWidget(self._lbl)
		self._lbl.setAlignment(Qt.AlignCenter)
		self.setAutoFillBackground(True)
		self.setBackgroundRole(self.palette().Shadow)
		self.setContentsMargins(-10,-10,-10,-10)
		self._click = False
		self._override_hide = False

	def mousePressEvent(self, event):
		if self._click:
			self.clicked.emit()
		return super().mousePressEvent(event)

	def set_clickable(self, d=True):
		self._click = d
		self.setCursor(Qt.PointingHandCursor)

	def resize(self, x, y=0):
		return super().resize(x, self._default_height)

	def add_text(self, text, autohide=True):
		"""
		Add new text to the bar, deleting the previous one
		"""
		try:
			self._reset()
		except TypeError:
			pass
		if not self.isVisible():
			self.show()
		self._lbl.setText(text)
		if autohide:
			if not self._override_hide:
				QTimer.singleShot(10000, self.hide)

	def begin_show(self):
		"""
		Control how long you will show notification bar.
		end_show() must be called to hide the bar.
		"""
		self._override_hide = True
		self.show()

	def end_show(self):
		self._override_hide = False
		QTimer.singleShot(5000, self.hide)

	def _reset(self):
		self.unsetCursor()
		self._click = False
		self.clicked.disconnect()

class GalleryShowcaseWidget(QWidget):
	"""
	Pass a gallery or set a gallery via -> set_gallery
	"""
	def __init__(self, gallery=None, parent=None):
		super().__init__(parent)
		self.main_layout = QVBoxLayout(self)
		self.profile = QLabel()
		self.text = QLabel()
		self.font_M = self.text.fontMetrics()
		self.main_layout.addWidget(self.profile)
		self.main_layout.addWidget(self.text)
		self.h = 0
		self.w = 0
		if gallery:
			self.h = 220
			self.w = 143
			self.set_gallery(gallery, (self.w, self.h))
		self.resize(self.w, self.h)

	def set_gallery(self, gallery, size=(143, 220)):
		assert isinstance(size, (list, tuple))
		self.w = size[0]
		self.h = size[1]
		self.profile.setPixmap(QPixmap(gallery.profile).scaled(self.w, self.h-20, Qt.KeepAspectRatio, Qt.SmoothTransformation))
		title = self.font_M.elidedText(gallery.title, Qt.ElideRight, self.w)
		artist = self.font_M.elidedText(gallery.artist, Qt.ElideRight, self.w)
		self.text.setText("{}\n{}".format(title, artist))
		self.resize(self.w, self.h)

class SingleGalleryChoices(BasePopup):
	"""
	Represent a single gallery with a list of choices below.
	Pass a gallery and a list of tuple/list where the first index is a string in each
	if text is passed, the text will be shown alongside gallery, else gallery be centered
	"""
	USER_CHOICE = pyqtSignal(tuple)
	def __init__(self, gallery, tuple_first_idx, text=None, parent = None):
		super().__init__(parent, flags= Qt.Dialog | Qt.FramelessWindowHint)
		main_layout = QVBoxLayout()
		self.main_widget.setLayout(main_layout)
		g_showcase = GalleryShowcaseWidget()
		g_showcase.set_gallery(gallery, (170//1.40, 170))
		if text:
			t_layout = QHBoxLayout()
			main_layout.addLayout(t_layout)
			t_layout.addWidget(g_showcase, 1)
			info = QLabel(text)
			info.setWordWrap(True)
			t_layout.addWidget(info)
		else:
			main_layout.addWidget(g_showcase, 0, Qt.AlignCenter)
		self.list_w = QListWidget(self)
		main_layout.addWidget(self.list_w, 3)
		main_layout.addLayout(self.buttons_layout)
		for t in tuple_first_idx:
			item = GalleryListItem(t)
			item.setText(t[0])
			self.list_w.addItem(item)
		buttons = self.add_buttons('Choose')
		buttons[0].clicked.connect(self.finish)
		self.resize(400, 400)
		self.show()

	def finish(self):
		item = self.list_w.selectedItems()
		if item:
			item = item[0]
			self.USER_CHOICE.emit(item.gallery)
			self.close()

class LoadingOverlay(QWidget):
	
	def __init__(self, parent=None):
		super().__init__(parent)
		palette = QPalette(self.palette())
		palette.setColor(palette.Background, Qt.transparent)
		self.setPalette(palette)

	def paintEngine(self, event):
		painter = QPainter()
		painter.begin(self)
		painter.setRenderHint(QPainter.Antialiasing)
		painter.fillRect(event.rect(),
				   QBrush(QColor(255,255,255,127)))
		painter.setPen(QPen(Qt.NoPen))
		for i in range(6):
			if (self.counter/5) % 6 == i:
				painter.setBrush(QBrush(QColor(127+
								   (self.counter%5)*32,127,127)))
			else:
				painter.setBrush(QBrush(QColor(127,127,127)))
				painter.drawEllipse(self.width()/2+30*
						math.cos(2*math.pi*i/6.0) - 10,
						self.height()/2+30*
						math.sin(2*math.pi*i/6.0) - 10,
						20,20)

		painter.end()

	def showEvent(self, event):
		self.timer = self.startTimer(50)
		self.counter = 0
		super().showEvent(event)

	def timerEvent(self, event):
		self.counter += 1
		self.update()
		if self.counter == 60:
			self.killTimer(self.timer)
			self.hide()

class FileIcon:

	@staticmethod
	def get_file_icon(path):
		# TODO: Very ineffiecent!! Save known file exts
		info = QFileInfo(path)
		return QFileIconProvider().icon(info)

	@staticmethod
	def get_external_file_icon():
		if gui_constants._REFRESH_EXTERNAL_VIEWER:
			if os.path.exists(gui_constants.GALLERY_EXT_ICO_PATH):
				os.remove(gui_constants.GALLERY_EXT_ICO_PATH)
			info = QFileInfo(gui_constants.EXTERNAL_VIEWER_PATH)
			icon =  QFileIconProvider().icon(info)
			pixmap = icon.pixmap(QSize(32, 32))
			pixmap.save(gui_constants.GALLERY_EXT_ICO_PATH, quality=100)
			gui_constants._REFRESH_EXTERNAL_VIEWER = False

		return QIcon(gui_constants.GALLERY_EXT_ICO_PATH)

	@staticmethod
	def refresh_default_icon():

		if os.path.exists(gui_constants.GALLERY_DEF_ICO_PATH):
			os.remove(gui_constants.GALLERY_DEF_ICO_PATH)

		def get_file(n):
			gallery = gallerydb.GalleryDB.get_gallery_by_id(n)
			if not gallery:
				return False
			file = ""
			if gallery.path.endswith(tuple(ARCHIVE_FILES)):
				zip = ArchiveFile(gallery.path)
				for name in zip.namelist():
					if name.endswith(tuple(IMG_FILES)):
						folder = os.path.join(
							gui_constants.temp_dir,
							'{}{}'.format(name, n))
						zip.extract(name, folder)
						file = os.path.join(
							folder, name)
						break;
			else:
				for name in os.listdir(gallery.chapters[0]):
					if name.endswith(tuple(IMG_FILES)):
						file = os.path.join(
							gallery.chapters[0], name)
						break;
			return file

		# TODO: fix this! (When there are no ids below 300? (because they go deleted))
		for x in range(1, 300):
			try:
				file = get_file(x)
				break
			except FileNotFoundError:
				continue
			except CreateZipFail:
				continue

		if not file:
			return None
		icon = QFileIconProvider().icon(QFileInfo(file))
		pixmap = icon.pixmap(QSize(32, 32))
		pixmap.save(gui_constants.GALLERY_DEF_ICO_PATH, quality=100)
		return True

	@staticmethod
	def get_default_file_icon():
		s = True
		if not os.path.isfile(gui_constants.GALLERY_DEF_ICO_PATH):
			s = FileIcon.refresh_default_icon()
		if s:
			return QIcon(gui_constants.GALLERY_DEF_ICO_PATH)
		else: return None

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

    def __init__(self, parent=None, margin=0, spacing=-1):
        super(FlowLayout, self).__init__(parent)

        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)

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
        return True

    def heightForWidth(self, width):
        height = self.doLayout(QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()

        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())

        margin, _, _, _ = self.getContentsMargins()

        size += QSize(2 * margin, 2 * margin)
        return size

    def doLayout(self, rect, testOnly):
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

class LineEdit(QLineEdit):
	"""
	Custom Line Edit which sacrifices contextmenu for selectAll
	"""
	def __init__(self, parent=None):
		super().__init__(parent)

	def mousePressEvent(self, event):
		if event.button() == Qt.RightButton:
			self.selectAll()
		else:
			super().mousePressEvent(event)

	def contextMenuEvent(self, QContextMenuEvent):
		pass

class PathLineEdit(QLineEdit):
	"""
	A lineedit which open a filedialog on right/left click
	Set dir to false if you want files.
	"""
	def __init__(self, parent=None, dir=True):
		super().__init__(parent)
		self.folder = dir
		self.setPlaceholderText('Right/Left-click to open folder explorer.')
		self.setToolTip('Right/Left-click to open folder explorer.')

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
		lbl = QLabel('{} by {}'.format(gallery.title, gallery.artist))
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

