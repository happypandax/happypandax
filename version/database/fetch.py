import os
import time

from .db_constants import SERIES_PATH, IMG_FILES

from .seriesdb import Series

from PyQt5.QtCore import QObject, Qt, pyqtSignal, pyqtSlot  # need this for interaction to mainloop
from PyQt5.QtGui import QPixmap

"""This file contains functions to fectch series data"""

class Fetch(QObject):
	"""A class containing methods to fetch series data.
	Should be executed in a new thread.
	Contains following methods:
	local -> runs a local search in the given SERIES_PATH
	"""

	FINISHED = pyqtSignal(bool)
	DATA_COUNT = pyqtSignal(int)
	DATA_READY = pyqtSignal(list)
	PROGRESS = pyqtSignal(int)

	def __init__(self, parent=None):
		super().__init__(parent)
		#self.found_series = []
	
	def local(self):
		"""Do a local search in the given SERIES_PATH.
		TODO: Return bool for indicating success; Add found series
				dynamically.
		"""

		found_series = []
		print("Starting search")
		series_l = sorted(os.listdir(SERIES_PATH)) #list of folders in the "Series" folder 
		print(len(series_l))
		if len(series_l) != 0: # if series folder is not empty
			self.DATA_COUNT.emit(len(series_l)) #tell model how many items are going to be added
			progress = 0
			for ser_path in series_l: # ser_path = series folder title
				#new_series = Series() just trying something
				metadata = {}
				print(ser_path)
		
				path = os.path.join(SERIES_PATH, ser_path)
				metadata["path"] = path
				metadata["chapters"] = {}

				images_paths = []

				con = os.listdir(path) #all of content in the series folder
		
				chapters = [os.path.join(path,sub) for sub in con if os.path.isdir(os.path.join(path, sub))] #subfolders

				# if series has chapters divided into sub folders
				if len(chapters) != 0:
					for ch in chapters: #title of each chapter folder is a key to full path to the folder
						key = ch
						value = os.path.join(SERIES_PATH, ser_path, ch) #replace with a proper chapter class later
						metadata["chapters"][key] = value
		
					#pick first image of first chapter as the default title image
					first_cha = sorted(metadata["chapters"].keys())[0] #smallest chapter alphabetically
					f_cha_path = os.path.join(path,first_cha)
					for r,d,f in os.walk(f_cha_path):
						for file in f:
							if file[-3:] in IMG_FILES:
								images_paths.append(file)
				else: #else assume that all images are in series folder
					#f_cha_path = value # needed for finding first image below
					value = metadata["path"]
					for file in os.listdir(value):
						if file[-3:] in IMG_FILES:
							img_path = os.path.join(value, file)
							images_paths.append(img_path)
					metadata["chapters"] = images_paths
				
				#find last edited file
				times = set()
				for root, dirs, files in os.walk(path, topdown=False):
					for img in files:
						fp = os.path.join(root, img)
						times.add( os.path.getmtime(fp) )
				last_updated = time.asctime(time.gmtime(max(times)))
		
				f_img = sorted(images_paths)[0]
				#f_img = os.path.join(f_cha_path,img)


				#new_series.data["title"] = ser
				metadata["title"] = ser_path
				metadata["profile"] = f_img
				metadata["artist"] = "Anonymous" #TODO think up something later
				metadata["chapters_size"] = len(chapters)
				#new_series.data["last_update"] = last_updated
			#	for ch in chapters: #title of each chapter folder is a key to full path to the folder
			#		key = ch
			#		value = os.path.join(SERIES_PATH, ser, ch) #replace with a proper chapter class later
			#		new_series.chapters[key] = value
				progress += 1
				self.PROGRESS.emit(progress)
				#found_series.append(metadata)
				found_series.append([(metadata["title"], metadata["artist"]),
							  metadata["profile"]])
			

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

