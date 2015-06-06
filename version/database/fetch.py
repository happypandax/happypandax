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

import os, time
import re as regex
import logging

from .seriesdb import Series, SeriesDB
from .. import pewnet, settings, utils

from PyQt5.QtCore import QObject, pyqtSignal # need this for interaction with main thread

"""This file contains functions to fetch series data"""

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical

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
			log_d('Series folder is not empty')
			try:
				self.DATA_COUNT.emit(len(series_l)) #tell model how many items are going to be added
				log_d('Found {} items'.format(len(series_l)))
				progress = 0
				for ser_path in series_l: # ser_path = series folder title
					new_series = Series()

					path = os.path.join(self.series_path, ser_path)

					images_paths = []
					try:
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
						new_series.last_update = last_updated
						parsed = utils.title_parser(ser_path)
					except NotADirectoryError:
						if ser_path[-4:] == '.zip':
							#TODO: add support for folders in archive
							new_series.chapters[0] = path
							parsed = utils.title_parser(ser_path[:-4])
						else:
							log_w('Skipped {} in local search'.format(path))
							progress += 1 # update the progress bar
							self.PROGRESS.emit(progress)
							continue

					new_series.title = parsed['title']
					new_series.path = path
					new_series.artist = parsed['artist']
					new_series.language = parsed['language']
					new_series.info = "<i>No description..</i>"
					new_series.chapters_size = len(new_series.chapters)

					progress += 1 # update the progress bar
					self.PROGRESS.emit(progress)
					SeriesDB.add_series(new_series)
			except:
				log_e('Local Search: Fail')
				self.FINISHED.emit(False)
		else: # if series folder is empty
			log_e('Local search error: Invalid directory')
			log_d('Series folder is empty')
			self.FINISHED.emit(False)
			# might want to include an error message

		# everything went well
		log_i('Local search: OK')
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
			else:
				log_e('Invalid URL')
				return None

		new_url = http_checker(self.web_url)

		if website_checker(new_url) == 'exhen':
			self.WEB_PROGRESS.emit()
			cookie = settings.exhen_cookies()
			try:
				exhen = pewnet.ExHen(cookie[0], cookie[1])
			except IndexError:
				self.WEB_STATUS.emit(False)
				log_e('ExHentai: No cookies set')
				return None
			r_metadata(exhen.get_metadata([new_url]))
		elif website_checker(new_url) == 'ehen':
			self.WEB_PROGRESS.emit()
			ehen = pewnet.EHen()
			r_metadata(ehen.get_metadata([new_url]))
		else:
			log_e('Web Search: Fail')
			self.WEB_STATUS.emit(False)