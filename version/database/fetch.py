import os, time
import re as regex

from .seriesdb import Series, SeriesDB
from .. import pewnet, settings

from PyQt5.QtCore import QObject, pyqtSignal # need this for interaction with main thread

"""This file contains functions to fetch series data"""

class Fetch(QObject):
	"""A class containing methods to fetch series data.
	Should be executed in a new thread.
	Contains following methods:
	local -> runs a local search in the given series_path
	"""

	# local signals
	FINISHED = pyqtSignal(bool)
	DATA_COUNT = pyqtSignal(int)
	PROGRESS = pyqtSignal(int)

	# WEB signals
	WEB_METADATA = pyqtSignal(list)
	WEB_PROGRESS = pyqtSignal()
	WEB_STATUS = pyqtSignal(bool)

	def __init__(self, parent=None):
		super().__init__(parent)
		self.series_path = ""
		self.web_url = ""
	
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

	def web(self):
		"""Fetches gallery metadata from the web.
		Website is determined from the url"""

		assert len(self.web_url) > 5 # very random..

		def r_metadata(metadata):
			if metadata:
				self.WEB_METADATA.emit(metadata)
				self.WEB_STATUS.emit(True)
			else: self.WEB_STATUS.emit(False)

		def http_checker(url):
			try:
				r = regex.match('^(?=http)', url).group()
				del r
				return url
			except AttributeError:
				n_url = 'http://' + url
				return n_url

		def website_checker(url):
			if 'g.e-hentai.org' in url:
				return 'ehen'
			elif 'exhentai.org' in url:
				return 'exhen'
			else: return None

		new_url = http_checker(self.web_url)

		if website_checker(new_url) == 'exhen':
			self.WEB_PROGRESS.emit()
			cookie = settings.exhen_cookies()
			exhen = pewnet.ExHen(cookie[0], cookie[1])
			r_metadata(exhen.get_metadata([new_url]))
		elif website_checker(new_url) == 'ehen':
			self.WEB_PROGRESS.emit()
			ehen = pewnet.EHen()
			r_metadata(ehen.get_metadata([new_url]))
		else: self.WEB_STATUS.emit(False)