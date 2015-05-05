import os
import time
import uuid #for unique filename
import gc

from .db_constants import SERIES_PATH, IMG_FILES
from .seriesdb import Series
from ..gui import gui_constants

from PyQt5.QtCore import QObject, Qt, pyqtSignal, pyqtSlot, QDataStream, QFile, QIODevice
from PyQt5.QtGui import QImage

"""This file contains functions to fectch series data"""

class Fetch(QObject):
	"""A class containing methods to fetch series data.
	Should be executed in a new thread.
	Contains following methods:
	local -> runs a local search in the given SERIES_PATH
	gen_thumbnail -> generates thumbnail for an image, returns new img path
	"""

	FINISHED = pyqtSignal(bool)
	DATA_COUNT = pyqtSignal(int)
	DATA_READY = pyqtSignal(list)
	PROGRESS = pyqtSignal(int)

	def __init__(self, parent=None):
		super().__init__(parent)
		self.cache = "sad_cache" #cache dir name
	
	def local(self):
		"""Do a local search in the given SERIES_PATH.
		TODO: Return bool for indicating success; Add found series
				dynamically.
		"""

		found_series = []
		series_l = sorted(os.listdir(SERIES_PATH)) #list of folders in the "Series" folder 
		if len(series_l) != 0: # if series folder is not empty
			self.DATA_COUNT.emit(len(series_l)) #tell model how many items are going to be added
			progress = 0
			for ser_path in series_l: # ser_path = series folder title
				new_series = Series()
						
				path = os.path.join(SERIES_PATH, ser_path)
				new_series.path = path

				images_paths = []

				con = os.listdir(path) #all of content in the series folder
		
				chapters = [os.path.join(path,sub) for sub in con if os.path.isdir(os.path.join(path, sub))] #subfolders

				# if series has chapters divided into sub folders
				if len(chapters) != 0:
					for ch in chapters: #title of each chapter folder is a key to full path to the folder
						key = ch
						value = os.path.join(SERIES_PATH, ser_path, ch) #replace with a proper chapter class later
						new_series.chapters[key] = value
		
					#pick first image of first chapter as the default title image
					first_cha = sorted(new_series.chapters.keys())[0] #smallest chapter alphabetically
					f_cha_path = os.path.join(path,first_cha)
					for r,d,f in os.walk(f_cha_path):
						for file in f:
							if file[-3:] in IMG_FILES:
								images_paths.append(file)
				else: #else assume that all images are in series folder
					#f_cha_path = value # needed for finding first image below
					value = new_series.path
					for file in os.listdir(value):
						if file[-3:] in IMG_FILES:
							img_path = os.path.join(value, file)
							images_paths.append(img_path)
					new_series.path = images_paths
				
				#find last edited file
				times = set()
				for root, dirs, files in os.walk(path, topdown=False):
					for img in files:
						fp = os.path.join(root, img)
						times.add( os.path.getmtime(fp) )
				last_updated = time.asctime(time.gmtime(max(times)))
				
				#choose first image
				f_img = sorted(images_paths)[0]
				new_f_img = self.gen_thumbnail(f_img)


				new_series.title = ser_path
				new_series.profile = new_f_img
				new_series.artist = "Anonymous" #TODO think up something later
				new_series.data["chapters_size"] = len(chapters)
				#new_series.data["last_update"] = last_updated
			#	for ch in chapters: #title of each chapter folder is a key to full path to the folder
			#		key = ch
			#		value = os.path.join(SERIES_PATH, ser, ch) #replace with a proper chapter class later
			#		new_series.chapters[key] = value
				progress += 1
				self.PROGRESS.emit(progress)
				#found_series.append(metadata)
				found_series.append([(new_series.title, new_series.artist),
							  new_series.profile])
			

			self.DATA_READY.emit(found_series)
		
				#found_series.append(new_series)

		else: # if series folder is empty
			self.FINISHED.emit(False)
			# might want to include an error message

			#STRING = """NAME-:-{0} \nNUMBER_CHAPTERS-:-{1} \nLAST_EDITED-:-{2} \n""".format(name,len(chapters),last_edit)
			#f_path = os.path.join(path, C.MetaF)
			#f = open(f_path, 'w')    
			#f.write( STRING )
			#f.close()

		# everything went well
		self.FINISHED.emit(True)

	def gen_thumbnail(self, img_path, w=gui_constants.THUMB_W_SIZE-2,
				   h=gui_constants.THUMB_H_SIZE): # 2 and 6 to align it properly.. need to redo this
		"Generates new thumbnails with unique filename in the cache dir"
		# generate a cache dir if required
		suff = img_path[-4:] # the image ext with dot
		if not os.path.isdir(self.cache):
			os.mkdir(self.cache)

		# generate unique file name
		file_name = str(uuid.uuid4()) + suff
		new_img_path = self.cache + '/' + file_name # '\' is not supported by QFile
		
		# Do the scaling
		image = QImage()
		image.load(img_path)
		image = image.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
		image.save(new_img_path, quality=100)
		#del pixmap
		#gc.collect()
		abs_path = os.path.abspath(new_img_path)
		return abs_path
