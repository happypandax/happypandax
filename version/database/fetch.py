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
import logging, uuid, random

from .gallerydb import Gallery, GalleryDB
from ..gui import gui_constants
from .. import pewnet, settings, utils

from PyQt5.QtCore import QObject, pyqtSignal # need this for interaction with main thread

"""This file contains functions to fetch gallery data"""

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical

class Fetch(QObject):
	"""A class containing methods to fetch gallery data.
	Should be executed in a new thread.
	Contains following methods:
	local -> runs a local search in the given series_path
	"""

	# local signals
	FINISHED = pyqtSignal(object)
	DATA_COUNT = pyqtSignal(int)
	PROGRESS = pyqtSignal(int)

	# WEB signals
	WEB_METADATA = pyqtSignal(object)
	WEB_PROGRESS = pyqtSignal()
	WEB_STATUS = pyqtSignal(bool)

	def __init__(self, parent=None):
		super().__init__(parent)
		self.series_path = ""
		self.web_url = ""
		self.data = []
		self._curr_gallery = '' # for debugging purposes
		self._error = 'Unknown error' # for debugging purposes

		# web
		self.api_url = gui_constants.API_URL
		self.api_instance = pewnet.CustomAPI()
		self._use_ehen_api = gui_constants.FETCH_EHEN_API
		self._default_ehen_url = gui_constants.DEFAULT_EHEN_URL
		self.galleries = []

	def local(self):
		"""
		Do a local search in the given series_path.
		"""
		try:
			gallery_l = sorted(os.listdir(self.series_path)) #list of folders in the "Gallery" folder
			mixed = False
		except TypeError:
			gallery_l = self.series_path
			mixed = True
		if len(gallery_l) != 0: # if gallery path list is not empty
			log_d('Gallery folder is not empty')
			try:
				self.DATA_COUNT.emit(len(gallery_l)) #tell model how many items are going to be added
				log_d('Found {} items'.format(len(gallery_l)))
				progress = 0
				for ser_path in gallery_l: # ser_path = gallery folder title
					self._curr_gallery = ser_path
					if mixed:
						path = ser_path
						ser_path = os.path.split(path)[1]
					else:
						path = os.path.join(self.series_path, ser_path)
					if not GalleryDB.check_exists(ser_path):
						log_d('Creating gallery: {}'.format(ser_path.encode('utf-8', 'ignore')))
						new_gallery = Gallery()
						images_paths = []
						try:
							con = os.listdir(path) #all of content in the gallery folder
		
							chapters = sorted([os.path.join(path,sub) for sub in con if os.path.isdir(os.path.join(path, sub))]) #subfolders
							# if gallery has chapters divided into sub folders
							if len(chapters) != 0:
								for numb, ch in enumerate(chapters):
									chap_path = os.path.join(path, ch)
									new_gallery.chapters[numb] = chap_path

							else: #else assume that all images are in gallery folder
								new_gallery.chapters[0] = path
				
							#find last edited file
							times = set()
							for root, dirs, files in os.walk(path, topdown=False):
								for img in files:
									fp = os.path.join(root, img)
									times.add( os.path.getmtime(fp) )
							last_updated = time.asctime(time.gmtime(max(times)))
							new_gallery.last_update = last_updated
							parsed = utils.title_parser(ser_path)
						except NotADirectoryError:
							if ser_path[-4:] in utils.ARCHIVE_FILES:
								#TODO: add support for folders in archive
								new_gallery.chapters[0] = path
								parsed = utils.title_parser(ser_path[:-4])
							else:
								log_w('Skipped {} in local search'.format(path))
								progress += 1 # update the progress bar
								self.PROGRESS.emit(progress)
								continue

						new_gallery.title = parsed['title']
						new_gallery.path = path
						new_gallery.artist = parsed['artist']
						new_gallery.language = parsed['language']
						new_gallery.info = "<i>No description..</i>"
						new_gallery.chapters_size = len(new_gallery.chapters)

						self.data.append(new_gallery)
						log_d('Gallery successful created: {}'.format(ser_path.encode('utf-8', 'ignore')))
					else:
						log_d('Gallery already exists: {}'.format(ser_path.encode('utf-8', 'ignore')))

					progress += 1 # update the progress bar
					self.PROGRESS.emit(progress)
			except:
				log.exception('Local Search Error:')
				self.FINISHED.emit(False)
		else: # if gallery folder is empty
			log_e('Local search error: Invalid directory')
			log_d('Gallery folder is empty')
			self.FINISHED.emit(False)
			# might want to include an error message
		# everything went well
		log_i('Local search: OK')
		log_d('Created {} items'.format(len(self.data)))
		self.FINISHED.emit(self.data)

	def _append_custom_api(self, gallery):
		"""
		Appends the metadata to my custom api.
		Receives a gallery, or a list of gallery and metadata dict tuple pairs
		"""
		assert isinstance(gallery, (Gallery, list))
		pass

	def _get_metadata_api(self, gallery):
		"""
		Tries to retrieve metadata from my custom api,
		returns dict with keys 'success' and 'errors' with list of galleries as values
		"""
		assert isinstance(gallery, (Gallery, list))
		return {'success':None,'error':gallery}
		result = {'success':[],
			'error':[]}
		if isinstance(gallery, Gallery):
			pass
		else:
			pass

	def _return_gallery_metadata(galleries):
		"Emits galleries"
		assert isinstance(galleries, (Gallery, list))
		print('success')

	def auto_web_metadata(self):
		"""
		Auto fetches metadata for the provided list of galleries.
		Appends or replaces metadata with the new fetched metadata.
		"""
		if self.galleries:
			print('something')
			hashed_galleries = []
			hashes = []
			for gallery in self.galleries:
				hash = None
				if gui_constants.HASH_GALLERY_PAGES == 'all':
					if not gallery.hashes:
						if not gallery.gen_hashes():
							continue
					hash = gallery.hashes[random.randint(0, len(gallery.hashes)-1)]
				elif gui_constants.HASH_GALLERY_PAGES == '1':
					try:
						chap_path = gallery.chapters[0]
						imgs = os.listdir(chap_path)
						# filter
						img = [os.path.join(chap_path, x) for x in imgs\
							if x.endswith(tuple(utils.IMG_FILES))][len(imgs)//2]
						with open(img, 'rb') as f:
							hash = utils.generate_img_hash(f)
					except NotADirectoryError:
						zip = ArchiveFile(gallery.chapters[0])
						img = [x for x in zip.namelist()\
							if x.endswith(tuple(utils.IMG_FILES))][len(zip.namelist())//2]
						hash = utils.generate_img_hash(zip.open(img, fp=True))
					except FileNotFoundError:
						continue
				if not hash:
					print('not hash continuing')
					continue
				gallery.hash = hash
				print(hash)
				hashed_galleries.append(gallery)

			api_result = self._get_metadata_api(hashed_galleries)
			if api_result['success']:
				self._return_gallery_metadata(api_result(api_result['success']))

			if api_result['error']:
				print('api errored')
				error_galleries = api_result['error']
				if 'exhentai' in self._default_ehen_url:
					try:
						exprops = settings.ExProperties()
						if exprops.ipb_id and exprops.ipb_pass:
							hen = pewnet.ExHen(exprops.ipb_id, exprops.ipb_pass)
							valid_url = 'exhen'
						else:
							raise ValueError
					except ValueError:
						hen = pewnet.EHen()
						valid_url = 'ehen'
				else:
					hen = pewnet.EHen()
					valid_url = 'ehen'

				gallery_hashes = []
				checked_pre_url_galleries = []
				checked_galleries = []
				for gallery in error_galleries:
					if gallery.link:
						check = self.website_checker(gallery.link)
						if check == valid_url:
							checked_pre_url_galleries.append(gallery)
							continue
						else:
							log_i('Skipping because of predefined non ex/g.e-hentai url: {}'.
			format(gallery.title.encode()))
							continue
					checked_galleries.append(gallery)
					gallery_hashes.append(gallery.hash)

				# dict -> hash:[list of title,url tuples] or None
				print('finding urls')
				hen.LAST_USED = time.time()
				urls = hen.eh_hash_search(gallery_hashes)
				ready_galleries = []
				for gallery in checked_galleries:
					if not gallery.hash in urls:
						print('did not find url')
						continue
					title_url_list = urls[gallery.hash]
					if gui_constants.ALWAYS_CHOOSE_FIRST_HIT:
						title = title_url_list[0][0]
						url = title_url_list[0][1]
					else:
						# TODO: make user choose which gallery..
						pass
					gallery.temp_url = url
					ready_galleries.append(gallery)

				if checked_pre_url_galleries:
					ready_galleries += checked_pre_url_galleries
				final_galleries = []
				api_galleries = []
				if ready_galleries:
					print("Fetching metadata")
					for gallery in ready_galleries:
						print('next gallery')
						if not self._use_ehen_api:
							metadata = hen.eh_gallery_parser(gallery.url)
							if not metadata:
								log_e('No metadata found for gallery: {}'.format(gallery.title.encode()))
								continue
							api_galleries.append((gallery,metadata))
							if gui_constants.REPLACE_METADATA:
								gallery.type = metadata['type']
								gallery.language = metadata['language']
								gallery.pub_date = metadata['published']
								gallery.tags = metadata['tags']
							else:
								if not gallery.type:
									gallery.type = metadata['type']
								if not gallery.language:
									gallery.language = metadata['language']
								if not gallery.pub_date:
									gallery.pub_date = metadata['published']
								if not gallery.tags:
									gallery.tags = metadata['tags']
								else:
									for ns in metadata['tags']:
										if ns in gallery.tags:
											for tag in metadata['tags'][ns]:
												if not tag in gallery.tags[ns]:
													gallery.tags[ns].append(tag)
										else:
											gallery.tags[ns] = metadata['tags'][ns]
						else:
							raise NotImplementedError
				if api_galleries:
					self._append_custom_api(api_galleries)
				if final_galleries:
					print('everything went well with {} galleries'.format(len(final_galleries)))
					_return_gallery_metadata(final_galleries)
		print('Autometadata Done!')
		self.FINISHED.emit(True)

	def website_checker(self, url):
		if not url:
			return None

		if 'g.e-hentai.org' in url:
			return 'ehen'
		elif 'exhentai.org' in url:
			return 'exhen'
		else:
			log_e('Invalid URL')
			return None


	def web_metadata(self):
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

		def lock():
			t = 0
			while gui_constants.GLOBAL_EHEN_LOCK:
				time.sleep(0.5)
				t += 1
				if t > 1000:
					break;

		new_url = http_checker(self.web_url)

		if self.website_checker(new_url) == 'exhen':
			self.WEB_PROGRESS.emit()
			exprops = settings.ExProperties()
			if not exprops.ipb_id or not exprops.ipb_pass:
				self.WEB_STATUS.emit(False)
				log_e('ExHentai: No cookies properly set')
				return None
			lock()
			exhen = pewnet.ExHen(exprops.ipb_id, exprops.ipb_pass)
			if self._use_ehen_api:
				r_metadata(exhen.get_metadata([new_url]))
			else:
				r_metadata(exhen.eh_gallery_parser(new_url))
			exhen.end_lock()
		elif self.website_checker(new_url) == 'ehen':
			self.WEB_PROGRESS.emit()
			lock()
			ehen = pewnet.EHen()
			if self._use_ehen_api:
				r_metadata(ehen.get_metadata([new_url]))
			else:
				r_metadata(ehen.eh_gallery_parser(new_url))
			ehen.end_lock()
		else:
			log_e('Web Search: Fail')
			self.WEB_STATUS.emit(False)

