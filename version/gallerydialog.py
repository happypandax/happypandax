import queue, os, threading, random, logging, time, scandir
from datetime import datetime

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QDesktopWidget, QGroupBox,
							 QHBoxLayout, QFormLayout, QLabel, QLineEdit,
							 QPushButton, QProgressBar, QTextEdit, QComboBox,
							 QDateEdit, QFileDialog, QMessageBox, QScrollArea)
from PyQt5.QtCore import (pyqtSignal, Qt, QPoint, QDate, QThread, QTimer)

import app_constants
import utils
import gallerydb
import fetch
import misc

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical

class GalleryDialog(QWidget):
	"""
	A window for adding/modifying gallery.
	Pass a list of QModelIndexes to edit their data
	or pass a path to preset path
	"""

	SERIES = pyqtSignal(list)
	SERIES_EDIT = pyqtSignal(list, int)
	#gallery_list = [] # might want to extend this to allow mass gallery adding

	def __init__(self, parent=None, arg=None):
		super().__init__(parent, Qt.Dialog)
		self.setAttribute(Qt.WA_DeleteOnClose)
		self.parent_widget = parent
		log_d('Triggered Gallery Edit/Add Dialog')
		m_l = QVBoxLayout()
		self.main_layout = QVBoxLayout()
		dummy = QWidget(self)
		scroll_area = QScrollArea(self)
		scroll_area.setWidgetResizable(True)
		scroll_area.setFrameStyle(scroll_area.StyledPanel)
		dummy.setLayout(self.main_layout)
		scroll_area.setWidget(dummy)
		m_l.addWidget(scroll_area, 3)

		final_buttons = QHBoxLayout()
		final_buttons.setAlignment(Qt.AlignRight)
		m_l.addLayout(final_buttons)
		self.done = QPushButton("Done")
		self.done.setDefault(True)
		cancel = QPushButton("Cancel")
		final_buttons.addWidget(cancel)
		final_buttons.addWidget(self.done)

		def new_gallery():
			self.setWindowTitle('Add a new gallery')
			self.newUI()
			self.commonUI()
			self.done.clicked.connect(self.accept)
			cancel.clicked.connect(self.reject)

		if arg:
			if isinstance(arg, list):
				self.setWindowTitle('Edit gallery')
				self.position = arg[0].row()
				for index in arg:
					gallery = index.data(Qt.UserRole+1)
					self.commonUI()
					self.setGallery(gallery)
				self.done.clicked.connect(self.accept_edit)
				cancel.clicked.connect(self.reject_edit)
			elif isinstance(arg, str):
				new_gallery()
				self.choose_dir(arg)
		else:
			new_gallery()

		log_d('GalleryDialog: Create UI: successful')
		#TODO: Implement a way to mass add galleries
		#IDEA: Extend dialog in a ScrollArea with more forms...

		self.setLayout(m_l)
		self.resize(500,560)
		frect = self.frameGeometry()
		frect.moveCenter(QDesktopWidget().availableGeometry().center())
		self.move(frect.topLeft())
		#self.setAttribute(Qt.WA_DeleteOnClose)
		self._fetch_inst = fetch.Fetch()
		self._fetch_thread = QThread(self)
		self._fetch_thread.setObjectName("GalleryDialog metadata thread")
		self._fetch_inst.moveToThread(self._fetch_thread)
		self._fetch_thread.started.connect(self._fetch_inst.auto_web_metadata)

	def commonUI(self):
		f_web = QGroupBox("Metadata from the Web")
		f_web.setCheckable(False)
		self.main_layout.addWidget(f_web)
		web_main_layout = QVBoxLayout()
		web_info = misc.ClickedLabel("Which gallery URLs are supported? (hover)", parent=self)
		web_info.setToolTip(app_constants.SUPPORTED_METADATA_URLS)
		web_info.setToolTipDuration(999999999)
		web_main_layout.addWidget(web_info)
		web_layout = QHBoxLayout()
		web_main_layout.addLayout(web_layout)
		f_web.setLayout(web_main_layout)

		f_gallery = QGroupBox("Gallery Info")
		f_gallery.setCheckable(False)
		self.main_layout.addWidget(f_gallery)
		gallery_layout = QFormLayout()
		f_gallery.setLayout(gallery_layout)

		def basic_web(name):
			return QLabel(name), QLineEdit(), QPushButton("Get metadata"), QProgressBar()

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
		self.url_edit.setPlaceholderText("Insert supported gallery URLs or just press the button!")
		url_prog.hide()

		self.title_edit = QLineEdit()
		self.author_edit = QLineEdit()
		author_completer = misc.GCompleter(self, False, True, False)
		author_completer.setCaseSensitivity(Qt.CaseInsensitive)
		self.author_edit.setCompleter(author_completer)
		self.descr_edit = QTextEdit()
		self.descr_edit.setAcceptRichText(True)
		self.lang_box = QComboBox()
		self.lang_box.addItems(app_constants.G_LANGUAGES)
		self.lang_box.addItems(app_constants.G_CUSTOM_LANGUAGES)
		self._find_combobox_match(self.lang_box, app_constants.G_DEF_LANGUAGE, 0)
		tags_l = QVBoxLayout()
		tag_info = misc.ClickedLabel("How do i write namespace & tags? (hover)", parent=self)
		tag_info.setToolTip("Ways to write tags:\n\nNormal tags:\ntag1, tag2, tag3\n\n"+
					  "Namespaced tags:\nns1:tag1, ns1:tag2\n\nNamespaced tags with one or more"+
					  " tags under same namespace:\nns1:[tag1, tag2, tag3], ns2:[tag1, tag2]\n\n"+
					  "Those three ways of writing namespace & tags can be combined freely.\n"+
					  "Tags are seperated by a comma, NOT whitespace.\nNamespaces will be capitalized while tags"+
					  " will be lowercased.")
		tag_info.setToolTipDuration(99999999)
		tags_l.addWidget(tag_info)
		self.tags_edit = misc.CompleterTextEdit()
		self.tags_edit.setCompleter(misc.GCompleter(self, False, False))
		tags_l.addWidget(self.tags_edit, 3)
		self.tags_edit.setPlaceholderText("Press Tab to autocomplete (Ctrl + E to show popup)")
		self.type_box = QComboBox()
		self.type_box.addItems(app_constants.G_TYPES)
		self._find_combobox_match(self.type_box, app_constants.G_DEF_TYPE, 0)
		#self.type_box.currentIndexChanged[int].connect(self.doujin_show)
		#self.doujin_parent = QLineEdit()
		#self.doujin_parent.setVisible(False)
		self.status_box = QComboBox()
		self.status_box.addItems(app_constants.G_STATUS)
		self._find_combobox_match(self.status_box, app_constants.G_DEF_STATUS, 0)
		self.pub_edit = QDateEdit()
		self.pub_edit.setCalendarPopup(True)
		self.pub_edit.setDate(QDate.currentDate())
		self.path_lbl = misc.ClickedLabel("")
		self.path_lbl.setWordWrap(True)
		self.path_lbl.clicked.connect(lambda a: utils.open_path(a, a) if a else None)

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
		gallery_layout.addRow("Tags:", tags_l)
		gallery_layout.addRow("Type:", self.type_box)
		gallery_layout.addRow("Status:", self.status_box)
		gallery_layout.addRow("Publication Date:", self.pub_edit)
		gallery_layout.addRow("Path:", self.path_lbl)
		gallery_layout.addRow("Link:", link_layout)

		self.title_edit.setFocus()

	def resizeEvent(self, event):
		self.tags_edit.setFixedHeight(event.size().height()//8)
		self.descr_edit.setFixedHeight(event.size().height()//12.5)
		return super().resizeEvent(event)

	def _find_combobox_match(self, combobox, key, default):
		f_index = combobox.findText(key, Qt.MatchFixedString)
		if f_index != -1:
			combobox.setCurrentIndex(f_index)
		else:
			combobox.setCurrentIndex(default)

	def setGallery(self, gallery):
		"To be used for when editing a gallery"
		self.gallery = gallery

		self.url_edit.setText(gallery.link)

		self.title_edit.setText(gallery.title)
		self.author_edit.setText(gallery.artist)
		self.descr_edit.setText(gallery.info)

		self.tags_edit.setText(utils.tag_to_string(gallery.tags))


		self._find_combobox_match(self.lang_box, gallery.language, 2)
		self._find_combobox_match(self.type_box, gallery.type, 0)
		self._find_combobox_match(self.status_box, gallery.status, 0)

		gallery_pub_date = "{}".format(gallery.pub_date).split(' ')
		try:
			self.gallery_time = datetime.strptime(gallery_pub_date[1], '%H:%M:%S').time()
		except IndexError:
			pass
		qdate_pub_date = QDate.fromString(gallery_pub_date[0], "yyyy-MM-dd")
		self.pub_edit.setDate(qdate_pub_date)

		self.link_lbl.setText(gallery.link)
		self.path_lbl.setText(gallery.path)

	def newUI(self):

		f_local = QGroupBox("Directory/Archive")
		f_local.setCheckable(False)
		self.main_layout.addWidget(f_local)
		local_layout = QHBoxLayout()
		f_local.setLayout(local_layout)

		choose_folder = QPushButton("From Directory")
		choose_folder.clicked.connect(lambda: self.choose_dir('f'))
		local_layout.addWidget(choose_folder)

		choose_archive = QPushButton("From Archive")
		choose_archive.clicked.connect(lambda: self.choose_dir('a'))
		local_layout.addWidget(choose_archive)

		self.file_exists_lbl = QLabel()
		local_layout.addWidget(self.file_exists_lbl)
		self.file_exists_lbl.hide()

	def choose_dir(self, mode):
		"""
		Pass which mode to open the folder explorer in:
		'f': directory
		'a': files
		Or pass a predefined path
		"""
		self.done.show()
		self.file_exists_lbl.hide()
		if mode == 'a':
			name = QFileDialog.getOpenFileName(self, 'Choose archive',
											  filter=utils.FILE_FILTER)
			name = name[0]
		elif mode == 'f':
			name = QFileDialog.getExistingDirectory(self, 'Choose folder')
		elif mode:
			if os.path.exists(mode):
				name = mode
			else:
				return None
		if not name:
			return
		head, tail = os.path.split(name)
		name = os.path.join(head, tail)
		parsed = utils.title_parser(tail)
		self.title_edit.setText(parsed['title'])
		self.author_edit.setText(parsed['artist'])
		self.path_lbl.setText(name)
		if not parsed['language']:
			parsed['language'] = app_constants.G_DEF_LANGUAGE
		l_i = self.lang_box.findText(parsed['language'])
		if l_i != -1:
			self.lang_box.setCurrentIndex(l_i)
		if gallerydb.GalleryDB.check_exists(name):
			self.file_exists_lbl.setText('<font color="red">Gallery already exists.</font>')
			self.file_exists_lbl.show()
		# check galleries
		gs = 1
		if name.endswith(utils.ARCHIVE_FILES):
			gs = len(utils.check_archive(name))
		elif os.path.isdir(name):
			g_dirs, g_archs = utils.recursive_gallery_check(name)
			gs = len(g_dirs) + len(g_archs)
		if gs == 0:
			self.file_exists_lbl.setText('<font color="red">Invalid gallery source.</font>')
			self.file_exists_lbl.show()
			self.done.hide()
		if app_constants.SUBFOLDER_AS_GALLERY:
			if gs > 1:
				self.file_exists_lbl.setText('<font color="red">More than one galleries detected in source! Use other methods to add.</font>')
				self.file_exists_lbl.show()
				self.done.hide()

	def check(self):
		if len(self.title_edit.text()) is 0:
			self.title_edit.setFocus()
			self.title_edit.setStyleSheet("border-style:outset;border-width:2px;border-color:red;")
			return False
		elif len(self.author_edit.text()) is 0:
			self.author_edit.setText("Unknown")

		if len(self.path_lbl.text()) == 0 or self.path_lbl.text() == 'No path specified':
			self.path_lbl.setStyleSheet("color:red")
			self.path_lbl.setText('No path specified')
			return False

		return True

	def set_chapters(self, gallery_object, add_to_model=True):
		path = gallery_object.path
		chap_container = gallerydb.ChaptersContainer(gallery_object)
		metafile = utils.GMetafile()
		try:
			log_d('Listing dir...')
			con = scandir.scandir(path) # list all folders in gallery dir
			log_i('Gallery source is a directory')
			log_d('Sorting')
			chapters = sorted([sub.path for sub in con if sub.is_dir() or sub.name.endswith(utils.ARCHIVE_FILES)]) #subfolders
			# if gallery has chapters divided into sub folders
			if len(chapters) != 0:
				log_d('Chapters divided in folders..')
				for ch in chapters:
					chap = chap_container.create_chapter()
					chap.title = utils.title_parser(ch)['title']
					chap.path = os.path.join(path, ch)
					metafile.update(utils.GMetafile(chap.path))
					chap.pages = len(list(scandir.scandir(chap.path)))

			else: #else assume that all images are in gallery folder
				chap = chap_container.create_chapter()
				chap.title = utils.title_parser(os.path.split(path)[1])['title']
				chap.path = path
				metafile.update(utils.GMetafile(path))
				chap.pages = len(list(scandir.scandir(path)))

		except NotADirectoryError:
			if path.endswith(utils.ARCHIVE_FILES):
				gallery_object.is_archive = 1
				log_i("Gallery source is an archive")
				archive_g = sorted(utils.check_archive(path))
				for g in archive_g:
					chap = chap_container.create_chapter()
					chap.path = g
					chap.in_archive = 1
					metafile.update(utils.GMetafile(g, path))
					arch = utils.ArchiveFile(path)
					chap.pages = len(arch.dir_contents(g))
					arch.close()

		metafile.apply_gallery(gallery_object)
		if add_to_model:
			self.SERIES.emit([gallery_object])
			log_d('Sent gallery to model')
		

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
		self.link_lbl.setText(url)
		btn_widget.hide()
		pgr_widget.show()

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

		def gallery_picker(gallery, title_url_list, q):
			self.parent_widget._web_metadata_picker(gallery, title_url_list, q, self)

		try:
			dummy_gallery = self.make_gallery(self.gallery)
		except AttributeError:
			dummy_gallery = self.make_gallery(gallerydb.Gallery(), False)
		if not dummy_gallery:
			status(False)
			return None

		dummy_gallery._g_dialog_url = url
		self._fetch_inst.galleries = [dummy_gallery]
		self._disconnect()
		self._fetch_inst.GALLERY_PICKER.connect(gallery_picker)
		self._fetch_inst.GALLERY_EMITTER.connect(self.set_web_metadata)
		self._fetch_inst.FINISHED.connect(status)
		self._fetch_thread.start()
			
	def set_web_metadata(self, metadata):
		assert isinstance(metadata, gallerydb.Gallery)
		self.link_lbl.setText(metadata.link)
		self.title_edit.setText(metadata.title)
		self.author_edit.setText(metadata.artist)
		tags = ""
		lang = ['English', 'Japanese']
		self._find_combobox_match(self.lang_box, metadata.language, 2)
		self.tags_edit.setText(utils.tag_to_string(metadata.tags))
		pub_string = "{}".format(metadata.pub_date)
		pub_date = QDate.fromString(pub_string.split()[0], "yyyy-MM-dd")
		self.pub_edit.setDate(pub_date)
		self._find_combobox_match(self.type_box, metadata.type, 0)

	def make_gallery(self, new_gallery, add_to_model=True, new=False):
		if self.check():
			new_gallery.title = self.title_edit.text()
			log_d('Adding gallery title')
			new_gallery.artist = self.author_edit.text()
			log_d('Adding gallery artist')
			log_d('Adding gallery path')
			if new and app_constants.MOVE_IMPORTED_GALLERIES:
				app_constants.OVERRIDE_MONITOR = True
				new_gallery.path = utils.move_files(self.path_lbl.text())
			else:
				new_gallery.path = self.path_lbl.text()
			new_gallery.info = self.descr_edit.toPlainText()
			log_d('Adding gallery descr')
			new_gallery.type = self.type_box.currentText()
			log_d('Adding gallery type')
			new_gallery.language = self.lang_box.currentText()
			log_d('Adding gallery lang')
			new_gallery.status = self.status_box.currentText()
			log_d('Adding gallery status')
			new_gallery.tags = utils.tag_to_dict(self.tags_edit.toPlainText())
			log_d('Adding gallery: tagging to dict')
			qpub_d = self.pub_edit.date().toString("ddMMyyyy")
			dpub_d = datetime.strptime(qpub_d, "%d%m%Y").date()
			try:
				d_t = self.gallery_time
			except AttributeError:
				d_t = datetime.now().time().replace(microsecond=0)
			dpub_d = datetime.combine(dpub_d, d_t)
			new_gallery.pub_date = dpub_d
			log_d('Adding gallery pub date')
			new_gallery.link = self.link_lbl.text()
			log_d('Adding gallery link')
			if not new_gallery.chapters:
				log_d('Starting chapters')
				thread = threading.Thread(target=self.set_chapters, args=(new_gallery,add_to_model), daemon=True)
				thread.start()
				thread.join()
				log_d('Finished chapters')
			return new_gallery


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

	def _disconnect(self):
		try:
			self._fetch_inst.GALLERY_PICKER.disconnect()
			self._fetch_inst.GALLERY_EMITTER.disconnect()
			self._fetch_inst.FINISHED.disconnect()
		except TypeError:
			pass

	def delayed_close(self):
		if self._fetch_thread.isRunning():
			self._fetch_thread.finished.connect(self.close)
			self.hide()
		else:
			self.close()

	def accept(self):
		new_gallery = self.make_gallery(gallerydb.Gallery(), new=True)

		if new_gallery:
			self.delayed_close()

	def accept_edit(self):
		new_gallery = self.make_gallery(self.gallery)
		#for ser in self.gallery:
		if new_gallery:
			self.SERIES_EDIT.emit([new_gallery], self.position)
			self.delayed_close()

	def reject_edit(self):
		self.delayed_close()


