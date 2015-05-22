import os, time

from .seriesdb import Series, SeriesDB

from PyQt5.QtCore import QObject, pyqtSignal # need this for interaction with main thread

"""This file contains functions to fetch series data"""

class Fetch(QObject):
	"""A class containing methods to fetch series data.
	Should be executed in a new thread.
	Contains following methods:
	local -> runs a local search in the given series_path
	"""

	FINISHED = pyqtSignal(bool)
	DATA_COUNT = pyqtSignal(int)
	PROGRESS = pyqtSignal(int)

	def __init__(self, parent=None):
		super().__init__(parent)
		self.series_path = ""
	
	def local(self):
		"""Do a local search in the given series_path.
		"""
		series_l = sorted(os.listdir(self.series_path)) #list of folders in the "Series" folder 
		if len(series_l) != 0: # if series folder is not empty
			try:
				self.DATA_COUNT.emit(len(series_l)) #tell model how many items are going to be added
				progress = 0
				for ser_path in series_l: # ser_path = series folder title
					new_series = Series()

					path = os.path.join(self.series_path, ser_path)

					images_paths = []

					con = os.listdir(path) #all of content in the series folder
		
					chapters = sorted([os.path.join(path,sub) for sub in con if os.path.isdir(os.path.join(path, sub))]) #subfolders
					# if series has chapters divided into sub folders
					if len(chapters) != 0:
						for numb, ch in enumerate(chapters):
							chap_path = os.path.join(self.series_path, ser_path, ch)
							new_series.chapters[numb] = chap_path

					else: #else assume that all images are in series folder
						new_series.chapters[0] = path
				
					#find last edited file
					times = set()
					for root, dirs, files in os.walk(path, topdown=False):
						for img in files:
							fp = os.path.join(root, img)
							times.add( os.path.getmtime(fp) )
					last_updated = time.asctime(time.gmtime(max(times)))

					new_series.title = ser_path
					new_series.path = path
					new_series.artist = "Anon" #TODO: think up something later
					new_series.info = "<i>No description..</i>"
					new_series.chapters_size = len(chapters)
					new_series.last_update = last_updated

					progress += 1 # update the progress bar
					self.PROGRESS.emit(progress)
				
					SeriesDB.add_series(new_series)
			except:
				self.FINISHED.emit(False)
		else: # if series folder is empty
			self.FINISHED.emit(False)
			# might want to include an error message

		# everything went well
		self.FINISHED.emit(True)