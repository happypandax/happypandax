import os
import time

from .db_constants import SERIES_PATH, IMG_FILES

from .seriesdb import Series

from PyQt5.QtCore import QObject, Qt, pyqtSignal, pyqtSlot  # need this for interaction to mainloop

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
		self.found_series = []
	
	def local(self):
		"""Do a local search in the given SERIES_PATH.
		TODO: Return bool for indicating success; Add found series
				dynamically.
		"""

		#found_series = []
		print("Starting search")
		series_l = sorted(next(os.walk(SERIES_PATH))[1]) #list of folders in the "Series" folder 
		
		if len(series_l) != 0: # if series folder is not empty
			self.DATA_COUNT.emit(len(series_l)*2) #tell model how many items are going to be added
			progress = 0
			for ser in series_l: # ser = series folder title
				new_series = Series()
		
				path = os.path.join(SERIES_PATH,ser)

				images = []

				con = os.listdir(path) #all of content in the series folder
		
				chapters = next(os.walk(path))[1] #subfolders

				# if series has chapters divided into sub folders
				if len(chapters) != 0:
					for ch in chapters: #title of each chapter folder is a key to full path to the folder
						key = ch
						value = os.path.join(SERIES_PATH, ser, ch) #replace with a proper chapter class later
						new_series.chapters[key] = value
		
					#pick first image of first chapter as the default title image
					first_cha = sorted(new_series.chapters.keys())[0] #smallest chapter alphabetically
					f_cha_path = os.path.join(path,first_cha)
					for r,d,f in os.walk(f_cha_path):
						for file in f:
							if file[-3:] in IMG_FILES:
								images.append(file)
				else: #else assume that all images are in series folder
					value = os.path.join(SERIES_PATH, ser) #just add path to series
					f_cha_path = value # needed for finding first image below
					new_series.chapters[ser] = value
					for r,d,f in os.walk(value):
						for file in f:
							if file[-3:] in IMG_FILES:
								images.append(file)

				#find last edited file
				times = set()
				for root, dirs, files in os.walk(path, topdown=False):
					for img in files:
						fp = os.path.join(root, img)
						times.add( os.path.getmtime(fp) )
				last_updated = time.asctime(time.gmtime(max(times)))

		
				img = sorted(images)[0]
				f_img = os.path.join(f_cha_path,img)


				#new_series.data["title"] = ser
				new_series.title = ser
				new_series.title_image = f_img
				new_series.artist = "Anonymous" #TODO think up something later
				new_series.data["path"] = path
				new_series.data["number_of_chapters"] = len(chapters)
				new_series.data["last_update"] = last_updated
			#	for ch in chapters: #title of each chapter folder is a key to full path to the folder
			#		key = ch
			#		value = os.path.join(SERIES_PATH, ser, ch) #replace with a proper chapter class later
			#		new_series.chapters[key] = value
				progress += 1
				self.PROGRESS.emit(progress)
				self.found_series.append(new_series)
			

			self.DATA_READY.emit(self.found_series)
		
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

