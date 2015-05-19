from PyQt5.QtCore import Qt, QDate, QPoint, pyqtSignal
from PyQt5.QtWidgets import (QWidget, QProgressBar, QLabel,
							 QVBoxLayout, QHBoxLayout,
							 QDialog, QGridLayout, QLineEdit,
							 QFormLayout, QPushButton, QTextEdit,
							 QComboBox, QDateEdit, QGroupBox,
							 QDesktopWidget, QMessageBox, QFileDialog)
import os, threading, queue, time
from datetime import datetime
from ..utils import tag_to_string, tag_to_dict

class Loading(QWidget):
	ON = False #to prevent multiple instances
	def __init__(self):
		from ..constants import WINDOW as parent
		super().__init__(parent, Qt.FramelessWindowHint)
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
		self.move(parent.window().rect().center()-QPoint(120,50))

	def mousePressEvent(self, QMouseEvent):
		pass

	def setText(self, string):
		if string != self.text.text():
			self.text.setText(string)

class SeriesDialog(QDialog):
	"A window for adding/modifying series"

	series_queue = queue.Queue()
	SERIES = pyqtSignal(list)
	SERIES_EDIT = pyqtSignal(list, int)
	#series_list = [] # might want to extend this to allow mass series adding

	def _init__(self, parent=None):
		super().__init__()
	#TODO: Implement a way to mass add series'
	#IDEA: Extend dialog in a ScrollArea with more forms...

	def initUI(self):
		main_layout = QVBoxLayout()

		f_web = QGroupBox("From the Web")
		f_web.setCheckable(False)
		main_layout.addWidget(f_web)
		web_layout = QHBoxLayout()
		f_web.setLayout(web_layout)

		f_local = QGroupBox("From local folder")
		f_local.setCheckable(False)
		main_layout.addWidget(f_local)
		local_layout = QHBoxLayout()
		f_local.setLayout(local_layout)

		f_series = QGroupBox("Series Info")
		f_series.setCheckable(False)
		main_layout.addWidget(f_series)
		series_layout = QFormLayout()
		f_series.setLayout(series_layout)

		def basic_web(name):
			return QLabel(name), QLineEdit(), QPushButton("Fetch")

		exh_lbl, exh_edit, exh_btn = basic_web("ExHen:")
		web_layout.addWidget(exh_lbl, 0, Qt.AlignLeft)
		web_layout.addWidget(exh_edit, 0)
		web_layout.addWidget(exh_btn, 0, Qt.AlignRight)

		choose_folder = QPushButton("Choose Folder")
		choose_folder.clicked.connect(self.choose_dir)
		local_layout.addWidget(choose_folder, Qt.AlignLeft)

		self.title_edit = QLineEdit()
		self.title_edit.setFocus()
		self.author_edit = QLineEdit()
		self.descr_edit = QTextEdit()
		self.descr_edit.setFixedHeight(70)
		self.descr_edit.setPlaceholderText("HTML 4 tags are supported")
		self.lang_box = QComboBox()
		self.lang_box.addItems(["English", "Japanese", "Other"])
		self.lang_box.setCurrentIndex(0)
		self.tags_edit = QLineEdit()
		self.tags_edit.setPlaceholderText("namespace1:tag1, tag2, namespace3:tag3, etc..")
		self.type_box = QComboBox()
		self.type_box.addItems(["Manga", "Doujinshi", "Other"])
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
		self.path_lbl = QLabel("unspecified...")
		self.path_lbl.setWordWrap(True)

		series_layout.addRow("Title:", self.title_edit)
		series_layout.addRow("Author:", self.author_edit)
		series_layout.addRow("Description:", self.descr_edit)
		series_layout.addRow("Language:", self.lang_box)
		series_layout.addRow("Tags:", self.tags_edit)
		series_layout.addRow("Type:", self.type_box)
		series_layout.addRow("Publication Date:", self.pub_edit)
		series_layout.addRow("Path:", self.path_lbl)

		final_buttons = QHBoxLayout()
		final_buttons.setAlignment(Qt.AlignRight)
		main_layout.addLayout(final_buttons)
		done = QPushButton("Done")
		done.setDefault(True)
		done.clicked.connect(self.accept)
		cancel = QPushButton("Cancel")
		cancel.clicked.connect(self.reject)
		final_buttons.addWidget(cancel)
		final_buttons.addWidget(done)


		self.setLayout(main_layout)

	# TODO: complete this... maybe another time.. 
	#def doujin_show(self, index):
	#	if index is 1:
	#		self.doujin_parent.setVisible(True)
	#	else:
	#		self.doujin_parent.setVisible(False)

	def choose_dir(self):
		dir_name = QFileDialog.getExistingDirectory(self, 'Choose a folder')
		head, tail = os.path.split(dir_name)
		self.title_edit.setText(tail)
		self.path_lbl.setText(dir_name)

	def check(self):
		if len(self.title_edit.text()) is 0:
			self.title_edit.setFocus()
			self.title_edit.setStyleSheet("border-style:outset;border-width:2px;border-color:red;")
			return False
		elif len(self.author_edit.text()) is 0:
			self.author_edit.setText("Anon")

		if len(self.descr_edit.toPlainText()) is 0:
			self.descr_edit.setText("<i>No description..</i>")

		#if self.path_lbl.text() == "unspecified...":
		#	return False

		return True

	def accept(self):
		from ..database import seriesdb

		def do_chapters(series):
			thread = threading.Thread(target=self.set_chapters, args=(series,))
			thread.start()
			thread.join()
			return self.series_queue.get()

		if self.check():
			new_series = seriesdb.Series()
			new_series.title = self.title_edit.text()
			new_series.artist = self.author_edit.text()
			new_series.path = self.path_lbl.text()
			new_series.info = self.descr_edit.toPlainText()
			new_series.type = self.type_box.currentText()
			new_series.language = self.lang_box.currentText()
			new_series.status = self.status_box.currentText()
			new_series.tags = tag_to_dict(self.tags_edit.text())
			qpub_d = self.pub_edit.date().toString("ddMMyyyy")
			dpub_d = datetime.strptime(qpub_d, "%d%m%Y").date()
			new_series.pub_date = dpub_d

			if self.path_lbl.text() == "unspecified...":
				self.SERIES.emit([new_series])
			else:
				updated_series = do_chapters(new_series)
				#for ser in self.series:
				self.SERIES.emit([updated_series])
			super().accept()

	def set_chapters(self, series_object):
		path = series_object.path
		con = os.listdir(path) # list all folders in series dir
		chapters = sorted([os.path.join(path,sub) for sub in con if os.path.isdir(os.path.join(path, sub))]) #subfolders
		# if series has chapters divided into sub folders
		if len(chapters) != 0:
			for numb, ch in enumerate(chapters):
				chap_path = os.path.join(path, ch)
				series_object.chapters[numb] = chap_path

		else: #else assume that all images are in series folder
			series_object.chapters[0] = path
				
		#find last edited file
		times = set()
		for root, dirs, files in os.walk(path, topdown=False):
			for img in files:
				fp = os.path.join(root, img)
				times.add( os.path.getmtime(fp) )
		series_object.last_update = time.asctime(time.gmtime(max(times)))
		self.series_queue.put(series_object)
		return True

	def reject(self):
		if self.check():
			msgbox = QMessageBox()
			msgbox.setText("<font color='red'><b>Noo oniichan! You were about to add a new series.</b></font>")
			msgbox.setInformativeText("Do you really want to discard?")
			msgbox.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
			msgbox.setDefaultButton(QMessageBox.No)
			if msgbox.exec() == QMessageBox.Yes:
				super().reject()
		else:
			super().reject()

	def trigger(self, list_of_index=None):
		if not list_of_index:
			self.initUI()
		else:
			assert isinstance(list_of_index, list)
			self.position = list_of_index[0].row()
			for index in list_of_index:
				series = index.data(Qt.UserRole+1)
				self.setSeries(series)

		from ..constants import WINDOW as parent
		self.resize(500,200)
		frect = self.frameGeometry()
		frect.moveCenter(QDesktopWidget().availableGeometry().center())
		self.move(frect.topLeft()-QPoint(0,120))
		self.setAttribute(Qt.WA_DeleteOnClose)
		self.setWindowFlags(Qt.FramelessWindowHint)
		self.exec()


	def setSeries(self, series):
		"To be used for when editing a series"
		self.series = series
		main_layout = QVBoxLayout()

		f_web = QGroupBox("Fetch metadata from Web")
		f_web.setCheckable(False)
		main_layout.addWidget(f_web)
		web_layout = QHBoxLayout()
		f_web.setLayout(web_layout)

		f_series = QGroupBox("Series Info")
		f_series.setCheckable(False)
		main_layout.addWidget(f_series)
		series_layout = QFormLayout()
		f_series.setLayout(series_layout)

		def basic_web(name):
			return QLabel(name), QLineEdit(), QPushButton("Fetch")

		exh_lbl, exh_edit, exh_btn = basic_web("ExHen:")
		web_layout.addWidget(exh_lbl, 0, Qt.AlignLeft)
		web_layout.addWidget(exh_edit, 0)
		web_layout.addWidget(exh_btn, 0, Qt.AlignRight)

		self.title_edit = QLineEdit()
		self.title_edit.setText(series.title)
		self.author_edit = QLineEdit()
		self.author_edit.setText(series.artist)
		self.descr_edit = QTextEdit()
		self.descr_edit.setText(series.info)
		self.descr_edit.setAcceptRichText(True)
		self.descr_edit.setFixedHeight(70)
		self.lang_box = QComboBox()
		self.lang_box.addItems(["English", "Japanese", "Other"])
		if series.language is "English":
			self.lang_box.setCurrentIndex(0)
		elif series.language is "Japanese":
			self.lang_box.setCurrentIndex(1)
		else:
			self.lang_box.setCurrentIndex(2)

		self.tags_edit = QLineEdit() #TODO Finish this..
		self.tags_edit.setPlaceholderText("namespace1:tag1, tag2, namespace3:[tag3, tag4] etc..")
		self.tags_edit.setText(tag_to_string(series.tags))

		self.type_box = QComboBox()
		self.type_box.addItems(["Manga", "Doujinshi", "Other"])
		if series.type is "Manga":
			self.type_box.setCurrentIndex(0)
		elif series.type is "Doujinshi":
			self.type_box.setCurrentIndex(1)
		else:
			self.type_box.setCurrentIndex(2)
		#self.type_box.currentIndexChanged[int].connect(self.doujin_show)
		#self.doujin_parent = QLineEdit()
		#self.doujin_parent.setVisible(False)
		self.status_box = QComboBox()
		self.status_box.addItems(["Unknown", "Ongoing", "Completed"])
		if series.status is "Ongoing":
			self.status_box.setCurrentIndex(1)
		elif series.status is "Completed":
			self.status_box.setCurrentIndex(2)
		else:
			self.status_box.setCurrentIndex(0)

		self.pub_edit = QDateEdit() # TODO: Finish this..
		self.pub_edit.setCalendarPopup(True)
		series_pub_date = "{}".format(series.pub_date)
		qdate_pub_date = QDate.fromString(series_pub_date, "yyyy-MM-dd")
		self.pub_edit.setDate(qdate_pub_date)
		self.path_lbl = QLabel("unspecified...")
		self.path_lbl.setWordWrap(True)
		self.path_lbl.setText(series.path)

		series_layout.addRow("Title:", self.title_edit)
		series_layout.addRow("Author:", self.author_edit)
		series_layout.addRow("Description:", self.descr_edit)
		series_layout.addRow("Language:", self.lang_box)
		series_layout.addRow("Tags:", self.tags_edit)
		series_layout.addRow("Type:", self.type_box)
		series_layout.addRow("Publication Date:", self.pub_edit)
		series_layout.addRow("Path:", self.path_lbl)

		final_buttons = QHBoxLayout()
		final_buttons.setAlignment(Qt.AlignRight)
		main_layout.addLayout(final_buttons)
		done = QPushButton("Done")
		done.setDefault(True)
		done.clicked.connect(self.accept_edit)
		cancel = QPushButton("Cancel")
		cancel.clicked.connect(self.reject_edit)
		final_buttons.addWidget(cancel)
		final_buttons.addWidget(done)

		self.setLayout(main_layout)

	def accept_edit(self):

		if self.check():
			new_series = self.series
			new_series.title = self.title_edit.text()
			new_series.artist = self.author_edit.text()
			new_series.path = self.path_lbl.text()
			new_series.info = self.descr_edit.toPlainText()
			new_series.type = self.type_box.currentText()
			new_series.language = self.lang_box.currentText()
			new_series.status = self.status_box.currentText()
			new_series.tags = tag_to_dict(self.tags_edit.text())
			qpub_d = self.pub_edit.date().toString("ddMMyyyy")
			dpub_d = datetime.strptime(qpub_d, "%d%m%Y").date()
			new_series.pub_date = dpub_d

			#for ser in self.series:
			self.SERIES_EDIT.emit([new_series], self.position)
			super().accept()

	def reject_edit(self):
		super().reject()