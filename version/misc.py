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
import os, threading, queue, time, logging, math, random, functools, scandir
from datetime import datetime

from PyQt5.QtCore import (Qt, QDate, QPoint, pyqtSignal, QThread,
						  QTimer, QObject, QSize, QRect, QFileInfo,
						  QMargins, QPropertyAnimation, QRectF,
						  QTimeLine, QMargins, QPropertyAnimation, QByteArray)
from PyQt5.QtGui import (QTextCursor, QIcon, QMouseEvent, QFont,
						 QPixmapCache, QPalette, QPainter, QBrush,
						 QColor, QPen, QPixmap, QMovie, QPaintEvent, QFontMetrics)
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
							 QColorDialog, QScrollArea, QSystemTrayIcon,
							 QMenu, QGraphicsBlurEffect, QActionGroup)

from utils import (tag_to_string, tag_to_dict, title_parser, ARCHIVE_FILES,
					 ArchiveFile, IMG_FILES, CreateArchiveFail)
import utils
import gui_constants
import gallerydb
import fetch
import settings

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical

def clearLayout(layout):
	if layout != None:
		while layout.count():
			child = layout.takeAt(0)
			if child.widget() is not None:
				child.widget().deleteLater()
			elif child.layout() is not None:
				clearLayout(child.layout())

class ElidedLabel(QLabel):
	def paintEvent(self, event):
		painter = QPainter(self)
		metrics = QFontMetrics(self.font())
		elided = metrics.elidedText(self.text(), Qt.ElideRight, self.width())
		painter.drawText(self.rect(), self.alignment(), elided)

class BaseMoveWidget(QWidget):
	def __init__(self, parent=None, **kwargs):
		move_listener = kwargs.pop('move_listener', True)
		super().__init__(parent, **kwargs)
		self.parent_widget = parent
		self.setAttribute(Qt.WA_DeleteOnClose)
		if parent and move_listener:
			try:
				parent.move_listener.connect(self.update_move)
			except AttributeError:
				pass

	def update_move(self, new_size=None):
		if new_size:
			self.move(new_size)
			return
		if self.parent_widget:
			self.move(self.parent_widget.window().frameGeometry().center() -\
				self.window().rect().center())

class SortMenu(QMenu):
	def __init__(self, parent, mangaview):
		super().__init__(parent)
		self.manga_view = mangaview

		self.sort_actions = QActionGroup(self, exclusive=True)
		asc_desc_act = QAction("Asc/Desc", self)
		asc_desc_act.triggered.connect(self.asc_desc)
		s_title = self.sort_actions.addAction(QAction("Title", self.sort_actions, checkable=True))
		s_title.triggered.connect(functools.partial(self.manga_view.sort, 'title'))
		s_artist = self.sort_actions.addAction(QAction("Author", self.sort_actions, checkable=True))
		s_artist.triggered.connect(functools.partial(self.manga_view.sort, 'artist'))
		s_date = self.sort_actions.addAction(QAction("Date Added", self.sort_actions, checkable=True))
		s_date.triggered.connect(functools.partial(self.manga_view.sort, 'date_added'))
		s_pub_d = self.sort_actions.addAction(QAction("Date Published", self.sort_actions, checkable=True))
		s_pub_d.triggered.connect(functools.partial(self.manga_view.sort, 'pub_date'))
		s_times_read = self.sort_actions.addAction(QAction("Read Count", self.sort_actions, checkable=True))
		s_times_read.triggered.connect(functools.partial(self.manga_view.sort, 'times_read'))

		self.addAction(asc_desc_act)
		self.addSeparator()
		self.addAction(s_title)
		self.addAction(s_artist)
		self.addAction(s_date)
		self.addAction(s_pub_d)
		self.addAction(s_times_read)

		self.set_current_sort()

	def set_current_sort(self):
		def check_key(act, key):
			if self.manga_view.current_sort == key:
				act.setChecked(True)

		for act in self.sort_actions.actions():
			if act.text() == 'Title':
				check_key(act, 'title')
			elif act.text() == 'Artist':
				check_key(act, 'artist')
			elif act.text() == 'Date Added':
				check_key(act, 'date_added')
			elif act.text() == 'Date Published':
				check_key(act, 'pub_date')
			elif act.text() == 'Read Count':
				check_key(act, 'times_read')

	def asc_desc(self):
		if self.manga_view.sort_model.sortOrder() == Qt.AscendingOrder:
			self.manga_view.sort_model.sort(0, Qt.DescendingOrder)
		else:
			self.manga_view.sort_model.sort(0, Qt.AscendingOrder)

	def showEvent(self, event):
		self.set_current_sort()
		super().showEvent(event)

class ToolbarButton(QPushButton):
	def __init__(self, parent = None, txt=''):
		super().__init__(parent)
		self._text = ''
		self._font_metrics = self.fontMetrics()
		if txt:
			self.setText(txt)
		self._selected = False

	@property
	def selected(self):
		return self._selected

	@selected.setter
	def selected(self, b):
		self._selected = b
		self.update()

	def paintEvent(self, event):
		assert isinstance(event, QPaintEvent)
		painter = QPainter(self)
		painter.setPen(QColor(164,164,164,120))
		painter.setBrush(Qt.NoBrush)
		if self._selected:
			painter.setBrush(QBrush(QColor(164,164,164,120)))
		#painter.setPen(Qt.NoPen)
		painter.setRenderHint(painter.Antialiasing)
		but_rect = QRectF(2.5,2.5, self.width()-5, self.height()-5)
		select_rect = QRectF(0,0, self.width(), self.height())

		painter.drawRoundedRect(but_rect, 2.5,2.5)
		txt_to_draw = self._font_metrics.elidedText(self._text,
											  Qt.ElideRight, but_rect.width())
		text_rect = QRectF(but_rect.x()+8, but_rect.y(), but_rect.width()-1.5,
					 but_rect.height()-1.5)
		painter.setPen(QColor('white'))
		painter.drawText(text_rect, txt_to_draw)

		if self.underMouse():
			painter.save()
			painter.setPen(Qt.NoPen)
			painter.setBrush(QBrush(QColor(164,164,164,90)))
			painter.drawRoundedRect(select_rect, 5,5)
			painter.restore()

	def setText(self, txt):
		self._text = txt
		self.update()
		super().setText(txt)
		self.adjustSize()

	def text(self):
		return self._text
		

class TransparentWidget(BaseMoveWidget):
	def __init__(self, parent=None, **kwargs):
		super().__init__(parent, **kwargs)
		self.setAttribute(Qt.WA_TranslucentBackground)

class Spinner(TransparentWidget):
	"""
	Spinner widget
	"""
	activated = pyqtSignal()
	deactivated = pyqtSignal()
	about_to_show, about_to_hide = range(2)

	def __init__(self, parent=None):
		super().__init__(parent, flags=Qt.Window|Qt.FramelessWindowHint)
		self.setAttribute(Qt.WA_ShowWithoutActivating)
		self.fps = 21
		self.border = 2
		self.line_width = 5
		self.arc_length = 100
		self.seconds_per_spin = 1

		self.text = ''

		self._timer = QTimer(self)
		self._timer.timeout.connect(self._on_timer_timeout)

		# keep track of the current start angle to avoid 
		# unnecessary repaints
		self._start_angle = 0

		self.state_timer = QTimer()
		self.current_state = self.about_to_show
		self.state_timer.timeout.connect(super().hide)
		self.state_timer.setSingleShot(True)

		# animation
		property_b_array = QByteArray().append('windowOpacity')
		self.fade_animation = QPropertyAnimation(self, property_b_array)
		self.fade_animation.setDuration(800)
		self.fade_animation.setStartValue(0.0)
		self.fade_animation.setEndValue(1.0)
		self.setWindowOpacity(0.0)
		self.set_size(50)

	def set_size(self, w):
		self.setFixedWidth(w)
		self.setFixedHeight(w+self.fontMetrics().height())
		self.update()

	def set_text(self, txt):
		self.text = txt
		self.update()

	def paintEvent(self, event):
		# call the base paint event:
		super().paintEvent(event)

		painter = QPainter()
		painter.begin(self)
		try:
			painter.setRenderHint(QPainter.Antialiasing)

			txt_rect = QRectF(0,0,0,0)
			if not self.text:
				txt_rect.setHeight(self.fontMetrics().height())

			painter.save()
			painter.setPen(Qt.NoPen)
			painter.setBrush(QBrush(QColor(88,88,88,180)))
			painter.drawRoundedRect(QRect(0,0, self.width(), self.height() - txt_rect.height()), 5, 5)
			painter.restore()

			pen = QPen(QColor('#F2F2F2'))
			pen.setWidth(self.line_width)
			painter.setPen(pen)

			if self.text:
				text_elided = self.fontMetrics().elidedText(self.text, Qt.ElideRight, self.width()-5)
				txt_rect = painter.boundingRect(txt_rect, text_elided)

			border = self.border + int(math.ceil(self.line_width / 2.0))
			r = QRectF((txt_rect.height())/2, (txt_rect.height()/2),
			  self.width()-txt_rect.height(), self.width()-txt_rect.height())
			r.adjust(border, border, -border, -border)

			# draw the arc:    
			painter.drawArc(r, -self._start_angle * 16, self.arc_length * 16)

			# draw text if there is
			if self.text:
				painter.drawText(QRectF(5, self.height()-txt_rect.height()-2.5, txt_rect.width(), txt_rect.height()),
					 text_elided)

			r = None

		finally:
			painter.end()
			painter = None

	def showEvent(self, event):
		if not self._timer.isActive():
			self.fade_animation.start()
			self.current_state = self.about_to_show
			self.state_timer.stop()
			self.activated.emit()
			self._timer.start(1000 / max(1, self.fps))
		super().showEvent(event)

	def hideEvent(self, event):
		self._timer.stop()
		self.deactivated.emit()
		super().hideEvent(event)

	def before_hide(self):
		if self.current_state == self.about_to_hide:
			return
		self.current_state = self.about_to_hide
		self.state_timer.start(5000)

	def closeEvent(self, event):
		self._timer.stop()
		super().closeEvent(event)

	def _on_timer_timeout(self):
		if not self.isVisible():
			return

		# calculate the spin angle as a function of the current time so that all 
		# spinners appear in sync!
		t = time.time()
		whole_seconds = int(t)
		p = (whole_seconds % self.seconds_per_spin) + (t - whole_seconds)
		angle = int((360 * p)/self.seconds_per_spin)

		if angle == self._start_angle:
			return

		self._start_angle = angle
		self.update()

class GalleryMenu(QMenu):
	def __init__(self, view, index, gallery_model, app_window, selected_indexes=None):
		super().__init__(app_window)
		self.parent_widget = app_window
		self.view = view
		self.gallery_model = gallery_model
		self.index = index
		self.selected = selected_indexes
		if not self.selected:
			favourite_act = self.addAction('Favorite',
									 lambda: self.parent_widget.manga_list_view.favorite(self.index))
			favourite_act.setCheckable(True)
			if self.index.data(Qt.UserRole+1).fav:
				favourite_act.setChecked(True)
				favourite_act.setText('Unfavorite')
			else:
				favourite_act.setChecked(False)
		else:
			favourite_act = self.addAction('Favorite selected', self.favourite_select)
			favourite_act.setCheckable(True)
			f = []
			for idx in self.selected:
				if idx.data(Qt.UserRole+1).fav:
					f.append(True)
				else:
					f.append(False)
			if all(f):
				favourite_act.setChecked(True)
				favourite_act.setText('Unfavorite selected')
			else:
				favourite_act.setChecked(False)

		self.addSeparator()
		if not self.selected:
			chapters_menu = self.addAction('Chapters')
			open_chapters = QMenu(self)
			chapters_menu.setMenu(open_chapters)
			for number, chap_number in enumerate(range(len(
				index.data(Qt.UserRole+1).chapters)), 1):
				chap_action = QAction("Open chapter {}".format(number),
							 open_chapters,
							 triggered = functools.partial(
								 self.parent_widget.manga_list_view.open_chapter,
								 index,
								 chap_number))
				open_chapters.addAction(chap_action)
		if not self.selected:
			add_chapters = self.addAction('Add chapters', self.add_chapters)
		if self.selected:
			open_f_chapters = self.addAction('Open first chapters',
									lambda: self.parent_widget.manga_list_view.open_chapter(self.selected, 0))
		self.addSeparator()
		if not self.selected:
			get_metadata = self.addAction('Get metadata',
									lambda: self.parent_widget.get_metadata(index.data(Qt.UserRole+1)))
		else:
			gals = []
			for idx in self.selected:
				gals.append(idx.data(Qt.UserRole+1))
			get_select_metadata = self.addAction('Get metadata for selected',
										lambda: self.parent_widget.get_metadata(gals))
		self.addSeparator()
		if not self.selected:
			edit = self.addAction('Edit', lambda: self.parent_widget.manga_list_view.spawn_dialog(self.index))
			text = 'folder' if not self.index.data(Qt.UserRole+1).is_archive else 'archive'
			op_folder_act = self.addAction('Open {}'.format(text), self.op_folder)
		else:
			text = 'folders' if not self.index.data(Qt.UserRole+1).is_archive else 'archives'
			op_folder_select = self.addAction('Open {}'.format(text), lambda: self.op_folder(True))
		if self.index.data(Qt.UserRole+1).link and not self.selected:
			op_link = self.addAction('Open URL', self.op_link)
		if self.selected and all([idx.data(Qt.UserRole+1).link for idx in self.selected]):
			op_links = self.addAction('Open URLs', lambda: self.op_link(True))

		remove_act = self.addAction('Remove')
		remove_menu = QMenu(self)
		remove_act.setMenu(remove_menu)
		if not self.selected:
			remove_g = remove_menu.addAction('Remove gallery',
								lambda: self.view.remove_gallery([self.index]))
			remove_ch = remove_menu.addAction('Remove chapter')
			remove_ch_menu = QMenu(self)
			remove_ch.setMenu(remove_ch_menu)
			for number, chap_number in enumerate(range(len(
				self.index.data(Qt.UserRole+1).chapters)), 1):
				chap_action = QAction("Remove chapter {}".format(number),
						  remove_ch_menu,
						  triggered = functools.partial(
							  self.parent_widget.manga_list_view.del_chapter,
							  index,
							  chap_number))
				remove_ch_menu.addAction(chap_action)
		else:
			remove_select_g = remove_menu.addAction('Remove selected galleries', self.remove_selection)
		remove_menu.addSeparator()
		if not self.selected:
			remove_source_g = remove_menu.addAction('Remove gallery and files',
									   lambda: self.view.remove_gallery(
										   [self.index], True))
		else:
			remove_source_select_g = remove_menu.addAction('Remove selected galleries and their files',
										   lambda: self.remove_selection(True))
		self.addSeparator()
		if not self.selected:
			advanced = self.addAction('Advanced')
			adv_menu = QMenu(self)
			advanced.setMenu(adv_menu)
			change_cover = adv_menu.addAction('Change cover...', self.change_cover)

	def favourite_select(self):
		for idx in self.selected:
			self.parent_widget.manga_list_view.favorite(idx)

	def change_cover(self):
		gallery = self.index.data(Qt.UserRole+1)
		log_i('Attempting to change cover of {}'.format(gallery.title.encode(errors='ignore')))
		if gallery.is_archive:
			try:
				zip = utils.ArchiveFile(gallery.path)
			except utils.CreateArchiveFail:
				gui_constants.NOTIF_BAR.add_text('Attempt to change cover failed. Could not create archive.')
				return
			path = zip.extract_all()
		else:
			path = gallery.path

		new_cover = QFileDialog.getOpenFileName(self,
							'Select a new gallery cover',
							filter='Image (*.jpg *.bmp *.png)',
							directory=path)[0]
		if new_cover and new_cover.endswith(utils.IMG_FILES):
			os.remove(gallery.profile)
			gallery.profile = gallerydb.gen_thumbnail(gallery, img=new_cover)
			gallery._cache = None
			self.parent_widget.manga_list_view.replace_edit_gallery(gallery,
														   self.index.row())
			log_i('Changed cover successfully!')

	def remove_selection(self, source=False):
		self.view.remove_gallery(self.selected, source)

	def op_link(self, select=False):
		if select:
			for x in self.selected:
				gal = x.data(Qt.UserRole+1)
				utils.open_web_link(gal.link)
		else:
			utils.open_web_link(self.index.data(Qt.UserRole+1).link)
			

	def op_folder(self, select=False):
		if select:
			for x in self.selected:
				text = 'Opening archives...' if self.index.data(Qt.UserRole+1).is_archive else 'Opening folders...'
				self.view.STATUS_BAR_MSG.emit(text)
				gal = x.data(Qt.UserRole+1)
				utils.open_path(gal.path)
		else:
			text = 'Opening archive...' if self.index.data(Qt.UserRole+1).is_archive else 'Opening folder...'
			self.view.STATUS_BAR_MSG.emit(text)
			gal = self.index.data(Qt.UserRole+1)
			utils.open_path(gal.path)

	def add_chapters(self):
		def add_chdb(chaps_dict):
			gallery = self.index.data(Qt.UserRole+1)
			log_i('Adding new chapter for {}'.format(gallery.title.encode(errors='ignore')))
			gallerydb.add_method_queue(gallerydb.ChapterDB.add_chapters_raw, False, gallery.id, {'chapters_dict':chaps_dict})
			gallery = gallerydb.GalleryDB.get_gallery_by_id(gallery.id)
			self.gallery_model.replaceRows([gallery], self.index.row())
		ch_widget = ChapterAddWidget(self.index.data(Qt.UserRole+1), self.parent_widget)
		ch_widget.CHAPTERS.connect(add_chdb)
		ch_widget.show()

class SystemTray(QSystemTrayIcon):
	"""
	Pass True to minimized arg in showMessage method to only
	show message if application is minimized.
	"""
	def __init__(self, icon, parent=None):
		super().__init__(icon, parent=None)
		self.parent_widget = parent

	def showMessage(self, title, msg, icon=QSystemTrayIcon.Information,
				 msecs=10000, minimized=False):
		if minimized:
			if self.parent_widget.isMinimized():
				return super().showMessage(title, msg, icon, msecs)
		else:
			return super().showMessage(title, msg, icon, msecs)

class ClickedLabel(QLabel):
	"""
	A QLabel which emits clicked signal on click
	"""
	clicked = pyqtSignal()
	def __init__(self, s="", **kwargs):
		super().__init__(s, **kwargs)
		self.setCursor(Qt.PointingHandCursor)
		self.setTextInteractionFlags(Qt.LinksAccessibleByMouse | Qt.LinksAccessibleByKeyboard)

	def mousePressEvent(self, event):
		self.clicked.emit()
		return super().mousePressEvent(event)

class TagText(QPushButton):
	def __init__(self, *args, **kwargs):
		self.search_widget = kwargs.pop('search_widget', None)
		self.namespace = kwargs.pop('namespace', None)
		super().__init__(*args, **kwargs)
		if self.search_widget:
			if self.namespace:
				self.clicked.connect(lambda: self.search_widget.search('{}:{}'.format(self.namespace, self.text())))
			else:
				self.clicked.connect(lambda: self.search_widget.search('{}'.format(self.text())))

class BasePopup(TransparentWidget):
	graphics_blur = QGraphicsBlurEffect()
	def __init__(self, parent=None, **kwargs):
		if kwargs:
			super().__init__(parent, **kwargs)
		else:
			super().__init__(parent, flags= Qt.Dialog | Qt.FramelessWindowHint)
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
		self.curr_pos = QPoint()
		if parent:
			parent.setGraphicsEffect(self.graphics_blur)

		# animation
		property_b_array = QByteArray().append('windowOpacity')
		self.fade_animation = QPropertyAnimation(self, property_b_array)
		self.fade_animation.setDuration(800)
		self.fade_animation.setStartValue(0.0)
		self.fade_animation.setEndValue(1.0)
		self.setWindowOpacity(0.0)

	def mousePressEvent(self, event):
		self.curr_pos = event.pos()
		return super().mousePressEvent(event)

	def mouseMoveEvent(self, event):
		if event.buttons() == Qt.LeftButton:
			diff = event.pos() - self.curr_pos
			newpos = self.pos()+diff
			self.move(newpos)
		return super().mouseMoveEvent(event)

	def showEvent(self, event):
		self.activateWindow()
		self.fade_animation.start()
		self.graphics_blur.setEnabled(True)
		return super().showEvent(event)

	def closeEvent(self, event):
		self.graphics_blur.setEnabled(False)
		return super().closeEvent(event)

	def hideEvent(self, event):
		self.graphics_blur.setEnabled(False)
		return super().hideEvent(event)

	def add_buttons(self, *args):
		"""
		Pass names of buttons, from right to left.
		Returns list of buttons in same order as they came in.
		Note: Remember to add buttons_layout to main layout!
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
		self._dynamic_height = 0
		self._lbl = QLabel()
		self._main_layout.addWidget(self._lbl)
		self._lbl.setAlignment(Qt.AlignCenter)
		self.setAutoFillBackground(True)
		self.setBackgroundRole(self.palette().Shadow)
		self.setContentsMargins(-10,-10,-10,-10)
		self._click = False
		self._override_hide = False

		property_b_array = QByteArray().append('minimumHeight')
		self.slide_animation = QPropertyAnimation(self, property_b_array)
		self.slide_animation.setDuration(500)
		self.slide_animation.setStartValue(0)
		self.slide_animation.setEndValue(self._default_height)
		self.slide_animation.valueChanged.connect(self.set_dynamic_height)

	def set_dynamic_height(self, h):
		self._dynamic_height = h

	def mousePressEvent(self, event):
		if self._click:
			self.clicked.emit()
		return super().mousePressEvent(event)

	def set_clickable(self, d=True):
		self._click = d
		self.setCursor(Qt.PointingHandCursor)

	def resize(self, x, y=0):
		return super().resize(x, self._dynamic_height)

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
				t = threading.Timer(10, self.hide)
				t.start()

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

	def showEvent(self, event):
		self.slide_animation.start()
		return super().showEvent(event)

class GalleryShowcaseWidget(QWidget):
	"""
	Pass a gallery or set a gallery via -> set_gallery
	"""
	def __init__(self, gallery=None, parent=None):
		super().__init__(parent)
		self.setAttribute(Qt.WA_DeleteOnClose)
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

		pixm = QPixmap(gallery.profile)
		if pixm.isNull():
			pixm = QPixmap(gui_constants.NO_IMAGE_PATH)
		pixm = pixm.scaled(self.w, self.h-20, Qt.KeepAspectRatio, Qt.FastTransformation)
		self.profile.setPixmap(pixm)
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
	
	def __init__(self):
		self.ico_types = {}

	def get_file_icon(self, path):
		if os.path.isdir(path):
			if not 'dir' in self.ico_types:
				self.ico_types['dir'] = QFileIconProvider().icon(QFileInfo(path))
			return self.ico_types['dir']
		elif path.endswith(utils.ARCHIVE_FILES):
			suff = ''
			for s in utils.ARCHIVE_FILES:
				if path.endswith(s):
					suff = s
			if not suff in self.ico_types:
				self.ico_types[suff] = QFileIconProvider().icon(QFileInfo(path))
			return self.ico_types[suff]

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
				try:
					zip = ArchiveFile(gallery.path)
				except utils.CreateArchiveFail:
					return False
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
				for p in scandir.scandir(gallery.chapters[0]):
					if p.name.endswith(tuple(IMG_FILES)):
						file = p.path
						break;
			return file

		# TODO: fix this! (When there are no ids below 300? (because they go deleted))
		for x in range(1, 300):
			try:
				file = get_file(x)
				break
			except FileNotFoundError:
				continue
			except CreateArchiveFail:
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
	def __init__(self, parent=None, dir=True, filters=utils.FILE_FILTER):
		super().__init__(parent)
		self.folder = dir
		self.filters = filters
		self.setPlaceholderText('Right/Left-click to open folder explorer.')
		self.setToolTip('Right/Left-click to open folder explorer.')

	def openExplorer(self):
		if self.folder:
			path = QFileDialog.getExistingDirectory(self,
										   'Choose folder')
		else:
			path = QFileDialog.getOpenFileName(self,
									  'Choose file', filter=self.filters)
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
		self.setAttribute(Qt.WA_DeleteOnClose)
		self.current_chapters = len(gallery.chapters)
		self.added_chaps = 0

		layout = QFormLayout()
		self.setLayout(layout)
		lbl = QLabel('{} by {}'.format(gallery.title, gallery.artist))
		layout.addRow('Gallery:', lbl)
		layout.addRow('Current chapters:', QLabel('{}'.format(self.current_chapters)))

		new_btn = QPushButton('Add directory')
		new_btn.clicked.connect(lambda: self.add_new_chapter('f'))
		new_btn.adjustSize()
		new_btn_a = QPushButton('Add archive')
		new_btn_a.clicked.connect(lambda: self.add_new_chapter('a'))
		new_btn_a.adjustSize()
		add_btn = QPushButton('Finish')
		add_btn.clicked.connect(self.finish)
		add_btn.adjustSize()
		new_l = QHBoxLayout()
		new_l.addWidget(add_btn, 1, alignment=Qt.AlignLeft)
		new_l.addWidget(Spacer('h'))
		new_l.addWidget(new_btn, alignment=Qt.AlignRight)
		new_l.addWidget(new_btn_a, alignment=Qt.AlignRight)
		layout.addRow(new_l)

		frame = QFrame()
		frame.setFrameShape(frame.StyledPanel)
		layout.addRow(frame)

		self.chapter_l = QVBoxLayout()
		frame.setLayout(self.chapter_l)

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

	def add_new_chapter(self, mode):
		chap_layout = QHBoxLayout()
		self.added_chaps += 1
		curr_chap = self.current_chapters+self.added_chaps

		chp_numb = QSpinBox(self)
		chp_numb.setMinimum(curr_chap-1)
		chp_numb.setMaximum(curr_chap+1)
		chp_numb.setValue(curr_chap)
		curr_chap_lbl = QLabel('Chapter {}'.format(curr_chap))
		def ch_lbl(n): curr_chap_lbl.setText('Chapter {}'.format(n))
		chp_numb.valueChanged[int].connect(ch_lbl)
		if mode =='f':
			chp_path = PathLineEdit()
			chp_path.setPlaceholderText('Right/Left-click to open folder explorer.'+
									' Leave empty to not add.')
		elif mode == 'a':
			chp_path = PathLineEdit(dir=False)
			chp_path.setPlaceholderText('Right/Left-click to open folder explorer.'+
									' Leave empty to not add.')

		chp_path.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
		if mode == 'f':
			chap_layout.addWidget(QLabel('D'))
		elif mode == 'a':
			chap_layout.addWidget(QLabel('A'))
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
				line_edit = layout.itemAt(1).widget()
				spin_box = layout.itemAt(2).widget()
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
		self.setAttribute(Qt.WA_DeleteOnClose)
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
			f_folder = QPushButton('Add directories')
			f_folder.clicked.connect(self.from_folder)
			f_files = QPushButton('Add archives')
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
		self.view_list.setAlternatingRowColors(True)
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
		self.count = 0

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
		self.count += 1

	def update_count(self):
		self.setWindowTitle('Gallery List ({})'.format(self.count))

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
											 filter='Archives ({})'.format(utils.FILE_FILTER))
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

class Loading(BasePopup):
	ON = False #to prevent multiple instances
	def __init__(self, parent=None):
		super().__init__(parent)
		self.progress = QProgressBar()
		self.progress.setStyleSheet("color:white")
		self.text = QLabel()
		self.text.setAlignment(Qt.AlignCenter)
		self.text.setStyleSheet("color:white;background-color:transparent;")
		inner_layout_ = QVBoxLayout()
		inner_layout_.addWidget(self.text, 0, Qt.AlignHCenter)
		inner_layout_.addWidget(self.progress)
		self.main_widget.setLayout(inner_layout_)
		self.resize(300,100)
		#frect = self.frameGeometry()
		#frect.moveCenter(QDesktopWidget().availableGeometry().center())
		#self.move(parent.window().frameGeometry().topLeft() +
		#	parent.window().rect().center() -
		#	self.rect().center() - QPoint(self.rect().width(),0))
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
		self._completer = None
		log_d('Instantiate CompleterTextEdit: OK')

	def setCompleter(self, c):
		if self._completer is not None:
			self._completer.activated.disconnect()

		self._completer = c

		c.setWidget(self)
		c.setCompletionMode(QCompleter.PopupCompletion)
		c.setCaseSensitivity(Qt.CaseInsensitive)
		c.activated.connect(self.insertCompletion)

	def completer(self):
		return self._completer

	def insertCompletion(self, completion):
		if self._completer.widget() is not self:
			return

		tc = self.textCursor()
		extra = len(completion) - len(self._completer.completionPrefix())
		tc.movePosition(QTextCursor.Left)
		tc.movePosition(QTextCursor.EndOfWord)
		tc.insertText(completion[-extra:])
		self.setTextCursor(tc)

	def textUnderCursor(self):
		tc = self.textCursor()
		tc.select(QTextCursor.WordUnderCursor)

		return tc.selectedText()

	def focusInEvent(self, e):
		if self._completer is not None:
			self._completer.setWidget(self)

		super().focusInEvent(e)

	def keyPressEvent(self, e):
		if self._completer is not None and self._completer.popup().isVisible():
			# The following keys are forwarded by the completer to the widget.
			if e.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Escape, Qt.Key_Tab, Qt.Key_Backtab):
				e.ignore()
				# Let the completer do default behavior.
				return

		isShortcut = e.modifiers() == Qt.ControlModifier and e.key() == Qt.Key_E
		if self._completer is None or not isShortcut:
			# Do not process the shortcut when we have a completer.
			super().keyPressEvent(e)

		ctrlOrShift = e.modifiers() & (Qt.ControlModifier | Qt.ShiftModifier)
		if self._completer is None or (ctrlOrShift and len(e.text()) == 0):
			return

		eow = "~!@#$%^&*()_+{}|:\"<>?,./;'[]\\-="
		hasModifier = (e.modifiers() != Qt.NoModifier) and not ctrlOrShift
		completionPrefix = self.textUnderCursor()

		if not isShortcut and (hasModifier or len(e.text()) == 0 or len(completionPrefix) < 3 or e.text()[-1] in eow):
			self._completer.popup().hide()
			return

		if completionPrefix != self._completer.completionPrefix():
			self._completer.setCompletionPrefix(completionPrefix)
			self._completer.popup().setCurrentIndex(
					self._completer.completionModel().index(0, 0))

		cr = self.cursorRect()
		cr.setWidth(self._completer.popup().sizeHintForColumn(0) + self._completer.popup().verticalScrollBar().sizeHint().width())
		self._completer.complete(cr)

#class CompleterWithData(QCompleter):
#	"""
#	Instantiate a QCompleter with predefined data
#	"""
#	insertText = pyqtSignal(str)

#	def __init__(self, data, parent=None):
#		assert isinstance(data, list)
#		super().__init__(data, parent)
#		#self.activated[str].connect(self.changeCompletion)
#		self.setModelSorting(QCompleter.CaseInsensitivelySortedModel)
#		self.setCaseSensitivity(Qt.CaseInsensitive)
#		self.setWrapAround(False)
#		log_d('Instantiate CompleterWithData: OK')

#	#def changeCompletion(self, completion):
#	#	if completion.find('(') != -1:
#	#		completion = completion[:completion.find('(')]
#	#	#print(completion)
#	#	self.insertText.emit(completion)



def return_tag_completer_TextEdit(parent=None):
	ns = gallerydb.TagDB.get_all_ns()
	for t in gallerydb.TagDB.get_all_tags():
		ns.append(t)
	TextEditCompleter = CompleterTextEdit()
	comp = QCompleter(ns, parent)
	comp.setCaseSensitivity(Qt.CaseInsensitive)
	TextEditCompleter.setCompleter(comp)
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

