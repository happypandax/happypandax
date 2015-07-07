from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QDesktopWidget, QGroupBox,
							 QHBoxLayout, QFormLayout, QLabel, QLineEdit,
							 QPushButton, QProgressBar, QTextEdit, QComboBox,
							 QDateEdit, QFileDialog, QMessageBox)
from PyQt5.QtCore import pyqtSignal, Qt, QPoint, QDate, QThread, QTimer
from datetime import datetime

import queue, os, threading, random, logging, time

from . import gui_constants
from .misc import return_tag_completer_TextEdit
from ..utils import title_parser, tag_to_dict, tag_to_string, FILE_FILTER
from ..database import gallerydb, fetch

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

	gallery_queue = queue.Queue()
	SERIES = pyqtSignal(list)
	SERIES_EDIT = pyqtSignal(list, int)
	#gallery_list = [] # might want to extend this to allow mass gallery adding

	def __init__(self, parent=None, arg=None):
		super().__init__(parent, Qt.Dialog)
		log_d('Triggered Gallery Edit/Add Dialog')
		self.main_layout = QVBoxLayout()

		if arg:
			if isinstance(arg, list):
				self.position = arg[0].row()
				for index in arg:
					gallery = index.data(Qt.UserRole+1)
					self.commonUI()
					self.setGallery(gallery)
				self.done.clicked.connect(self.accept_edit)
				self.cancel.clicked.connect(self.reject_edit)
			elif isinstance(arg, str):
				self.newUI()
				self.commonUI()
				self.choose_dir(arg)
				self.done.clicked.connect(self.accept)
				self.cancel.clicked.connect(self.reject)
		else:
			self.newUI()
			self.commonUI()
			self.done.clicked.connect(self.accept)
			self.cancel.clicked.connect(self.reject)

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
		self.tags_edit.setPlaceholderText("Press Tab to autocomplete (Ctrl + Space to show popup)"+
									"\ntag1, namespace:tag2, namespace2:[tag3, tag4] etc..")
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

		self.lang_box.setCurrentIndex(2)
		if gallery.language:
			if gallery.language.lower() in "english":
					self.lang_box.setCurrentIndex(0)
			elif gallery.language.lower() in "japanese":
				self.lang_box.setCurrentIndex(1)

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

		choose_archive = QPushButton("From ZIP/CBZ")
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
		if mode == 'a':
			name = QFileDialog.getOpenFileName(self, 'Choose archive',
											  filter=FILE_FILTER)
			name = name[0]
		elif mode == 'f':
			name = QFileDialog.getExistingDirectory(self, 'Choose folder')
		elif mode:
			if os.path.exists(mode):
				name = mode
			else:
				return None
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
		thread.started.connect(f.web_metadata)
		f.WEB_STATUS.connect(status)
		f.WEB_STATUS.connect(lambda: f.deleteLater)
		f.WEB_STATUS.connect(lambda: thread.deleteLater)
		thread.start()

		gui_constants.GLOBAL_EHEN_LOCK = True
		def unlock():
			gui_constants.GLOBAL_EHEN_LOCK = False
		r_time = random.randint(5,5+self.TIME_RAND)
		QTimer.singleShot(r_time*1000, unlock)
			

	def set_web_metadata(self, metadata):
		assert isinstance(metadata, list) or isinstance(metadata, dict)
		if gui_constants.FETCH_METADATA_API:
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
		else:
			current_tags = tag_to_dict(self.tags_edit.toPlainText(),
									ns_capitalize=False)
			for ns in metadata['tags']:
				if ns in current_tags:
					ns_tags = current_tags[ns]
					for tag in metadata['tags'][ns]:
						if not tag in ns_tags:
							ns_tags.append(tag)
				else:
					current_tags[ns] = metadata['tags'][ns]
			current_tags_string = tag_to_string(current_tags)
			self.tags_edit.setText(current_tags_string)

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


