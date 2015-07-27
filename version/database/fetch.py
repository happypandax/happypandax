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
import logging, uuid, random , queue

from .gallerydb import Gallery, GalleryDB, add_method_queue
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
	auto_web_metadata -> does a search online for the given galleries and returns their metdata
	"""

	# local signals
	FINISHED = pyqtSignal(object)
	DATA_COUNT = pyqtSignal(int)
	PROGRESS = pyqtSignal(int)

	# WEB signals
	GALLERY_EMITTER = pyqtSignal(Gallery)
	AUTO_METADATA_PROGRESS = pyqtSignal(str)
	GALLERY_PICKER = pyqtSignal(object, list, queue.Queue)
	GALLERY_PICKER_QUEUE = queue.Queue()

	def __init__(self, parent=None):
		super().__init__(parent)
		self.series_path = ""
		self.data = []
		self._curr_gallery = '' # for debugging purposes
		self._error = 'Unknown error' # for debugging purposes

		# web
		self._default_ehen_url = gui_constants.DEFAULT_EHEN_URL
		self.galleries = []
		self.galleries_in_queue = []
		self.error_galleries = []

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
			log_i('Gallery folder is not empty')
			try:
				self.DATA_COUNT.emit(len(gallery_l)) #tell model how many items are going to be added
				log_i('Found {} items'.format(len(gallery_l)))
				progress = 0
				def create_gallery(path, folder_name, do_chapters=True):
					if not GalleryDB.check_exists(folder_name):
						log_i('Creating gallery: {}'.format(folder_name.encode('utf-8', 'ignore')))
						new_gallery = Gallery()
						images_paths = []
						try:
							con = os.listdir(path) #all of content in the gallery folder
							log_i('Gallery source is a directory')
							chapters = sorted([os.path.join(path,sub) for sub in con if os.path.isdir(os.path.join(path, sub))])\
							    if do_chapters else [] #subfolders
							# if gallery has chapters divided into sub folders
							if len(chapters) != 0:
								log_i('Gallery has chapters divided in directories')
								for numb, ch in enumerate(chapters):
									chap_path = os.path.join(path, ch)
									new_gallery.chapters[numb] = chap_path

							else: #else assume that all images are in gallery folder
								new_gallery.chapters[0] = path
				
							##find last edited file
							#times = set()
							#for root, dirs, files in os.walk(path, topdown=False):
							#	for img in files:
							#		fp = os.path.join(root, img)
							#		times.add( os.path.getmtime(fp) )
							#last_updated = time.asctime(time.gmtime(max(times)))
							#new_gallery.last_update = last_updated
							parsed = utils.title_parser(folder_name)
						except NotADirectoryError:
							if folder_name.endswith(utils.ARCHIVE_FILES):
								log_i('Gallery source is an archive')
								#TODO: add support for folders in archive
								new_gallery.chapters[0] = path
								parsed = utils.title_parser(folder_name[:-4])
							else:
								log_w('Skipped {} in local search'.format(path))

						new_gallery.title = parsed['title']
						new_gallery.path = path
						new_gallery.artist = parsed['artist']
						new_gallery.language = parsed['language']
						new_gallery.info = "No description.."
						new_gallery.chapters_size = len(new_gallery.chapters)

						self.data.append(new_gallery)
						log_i('Gallery successful created: {}'.format(folder_name.encode('utf-8', 'ignore')))
					else:
						log_i('Gallery already exists: {}'.format(folder_name.encode('utf-8', 'ignore')))

				for folder_name in gallery_l: # ser_path = gallery folder title
					self._curr_gallery = folder_name
					if mixed:
						path = folder_name
						folder_name = os.path.split(path)[1]
					else:
						path = os.path.join(self.series_path, folder_name)

					if not gui_constants.SUBFOLDER_AS_CHAPTERS:
						log_i("Treating each subfolder as gallery")
						if os.path.isdir(path):
							gallery_sources = []
							for root, subfolders, files in os.walk(path):
								if files:
									for f in files:
										if f.endswith(utils.ARCHIVE_FILES):
											gallery_sources.append(os.path.join(root, f))
									
									if not subfolders:
										gallery_probability = len(files)
										for f in files:
											if not f.endswith(utils.IMG_FILES):
												gallery_probability -= 1
										if gallery_probability >= len(files)//2:
											gallery_sources.append(root)

							for gs in gallery_sources:
								create_gallery(gs, os.path.split(gs)[1], False)
						elif path.endswith(utils.ARCHIVE_FILES):
							create_gallery(path, folder_name)
					else:
						log_i("Treating each subfolder as chapter")
						create_gallery(path, folder_name)

					progress += 1 # update the progress bar
					self.PROGRESS.emit(progress)
			except:
				log.exception('Local Search Error:')
				self.FINISHED.emit(False)
		else: # if gallery folder is empty
			log_e('Local search error: Invalid directory')
			log_e('Gallery folder is empty')
			self.FINISHED.emit(False)
			# might want to include an error message
		# everything went well
		log_i('Local search: OK')
		log_i('Created {} items'.format(len(self.data)))
		self.FINISHED.emit(self.data)

	def _return_gallery_metadata(self, gallery):
		"Emits galleries"
		assert isinstance(gallery, Gallery)
		if gallery:
			gallery.exed = 1
			self.GALLERY_EMITTER.emit(gallery)
			log_d('Success')

	def fetch_metadata(self, gallery, hen, proc=False):
		"""
		Puts gallery in queue for metadata fetching. Applies received galleries and sends
		them to gallery model.
		Set proc to true if you want to process the queue immediately
		"""
		log_i("Fetching metadata for gallery: {}".format(gallery.title.encode(errors='ignore')))
		log_i("Adding to queue: {}".format(gallery.title.encode(errors='ignore')))
		if proc:
			metadata = hen.add_to_queue(gallery.temp_url, True)
		else:
			metadata = hen.add_to_queue(gallery.temp_url)
		self.galleries_in_queue.append(gallery)

		if metadata == 0: # Gallery is now put in queue
			return None
		# We received something from get_metadata
		if not metadata: # metadata fetching failed
			self.error_galleries.append(gallery)
			log_i("An error occured while fetching metadata with gallery: {}".format(
				gallery.title.encode(errors='ignore')))
			return None
		self.AUTO_METADATA_PROGRESS.emit("Applying metadata...")

		for x, g in enumerate(self.galleries_in_queue, 1):
			try:
				data = metadata[g.temp_url]
			except KeyError:
				self.AUTO_METADATA_PROGRESS.emit("No metadata found for gallery: {}".format(g.title))
				self.error_galleries.append(g)
				log_w("No metadata found for gallery: {}".format(g.title.encode(errors='ignore')))
				continue
			log_i('({}/{}) Applying metadata for gallery: {}'.format(x, len(self.galleries_in_queue),
															g.title.encode(errors='ignore')))
			if gui_constants.USE_JPN_TITLE:
				try:
					title = data['title']['jpn']
				except KeyError:
					title = data['title']['def']
			else:
				title = data['title']['def']

			if 'Language' in data['tags']:
				try:
					lang = [x for x in data['tags']['Language'] if not x == 'translated'][0].capitalize()
				except IndexError:
					lang = ""
			else:
				lang = ""

			title_artist_dict = utils.title_parser(title)
			if gui_constants.REPLACE_METADATA:
				g.title = title_artist_dict['title']
				if title_artist_dict['artist']:
					g.artist = title_artist_dict['artist']
				g.language = title_artist_dict['language'].capitalize()
				if 'Artist' in data['tags']:
					g.artist = data['tags']['Artist'][0].capitalize()
				if lang:
					g.language = lang
				g.type = data['type']
				g.pub_date = data['pub_date']
				g.tags = data['tags']
				g.link = g.temp_url
			else:
				if not g.title:
					g.title = title_artist_dict['title']
				if not g.artist:
					g.artist = title_artist_dict['artist']
					if 'Artist' in data['tags']:
						g.artist = data['tags']['Artist'][0].capitalize()
				if not g.language:
					g.language = title_artist_dict['language'].capitalize()
					if lang:
						g.language = lang
				if not g.type or g.type == 'Other':
					g.type = data['type']
				if not g.pub_date:
					g.pub_date = data['pub_date']
				if not g.tags:
					g.tags = data['tags']
				else:
					for ns in data['tags']:
						if ns in g.tags:
							for tag in data['tags'][ns]:
								if not tag in g.tags[ns]:
									g.tags[ns].append(tag)
						else:
							g.tags[ns] = data['tags'][ns]
				if not g.link:
					g.link = g.temp_url
			self._return_gallery_metadata(g)
			log_i('Successfully applied metadata to gallery: {}'.format(g.title.encode(errors='ignore')))
		self.galleries_in_queue.clear()
		self.AUTO_METADATA_PROGRESS.emit('Finished applying metadata')
		log_i('Finished applying metadata')
		
		#HTML PARSING OBSELETE
		#metadata = hen.eh_gallery_parser(gallery.temp_url)
		#if not metadata:
		#	self.AUTO_METADATA_PROGRESS('No metadata found for gallery: {}'.format(gallery.title))
		#	log_w('No metadata found for gallery: {}'.format(gallery.title.encode(errors='ignore')))
		#	return False
		#self.AUTO_METADATA_PROGRESS.emit("Applying metadata..")
		#log_i('Applying metadata')
		#title_artist_dict = utils.title_parser(metadata['title'])
		#if gui_constants.REPLACE_METADATA:
		#	gallery.title = title_artist_dict['title']
		#	if title_artist_dict['artist']:
		#		gallery.artist = title_artist_dict['artist']
		#	gallery.type = metadata['type']
		#	gallery.language = metadata['language']
		#	gallery.pub_date = metadata['published']
		#	gallery.tags = metadata['tags']
		#else:
		#	if not gallery.title:
		#		gallery.title = title_artist_dict['title']
		#	if not gallery.artist:
		#		gallery.artist = title_artist_dict['artist']
		#	if not gallery.type:
		#		gallery.type = metadata['type']
		#	if not gallery.language:
		#		gallery.language = metadata['language']
		#	if not gallery.pub_date:
		#		gallery.pub_date = metadata['published']
		#	if not gallery.tags:
		#		gallery.tags = metadata['tags']
		#	else:
		#		for ns in metadata['tags']:
		#			if ns in gallery.tags:
		#				for tag in metadata['tags'][ns]:
		#					if not tag in gallery.tags[ns]:
		#						gallery.tags[ns].append(tag)
		#			else:
		#				gallery.tags[ns] = metadata['tags'][ns]

	def auto_web_metadata(self):
		"""
		Auto fetches metadata for the provided list of galleries.
		Appends or replaces metadata with the new fetched metadata.
		"""
		log_i('Initiating auto metadata fetcher')
		if self.galleries and not gui_constants.GLOBAL_EHEN_LOCK:
			log_i('Auto metadata fetcher is now running')
			gui_constants.GLOBAL_EHEN_LOCK = True
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
			hen.LAST_USED = time.time()
			self.AUTO_METADATA_PROGRESS.emit("Checking gallery urls...")

			error_galleries = []
			fetched_galleries = []
			checked_pre_url_galleries = []
			for x, gallery in enumerate(self.galleries, 1):
				self.AUTO_METADATA_PROGRESS.emit("({}/{}) Generating gallery hash: {}".format(x, len(self.galleries), gallery.title))
				hash = None
				if gui_constants.HASH_GALLERY_PAGES == 'all':
					if not gallery.hashes:
						result = add_method_queue(gallery.gen_hashes, False)
						if not result:
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
						self.AUTO_METADATA_PROGRESS
						continue
				if not hash:
					error_galleries.append(gallery)
					log_e("Could not generate hash for gallery: {}".format(gallery.title.encode(errors='ignore')))
					continue
				gallery.hash = hash

				log_i("Checking gallery url")
				if gallery.link:
					check = self.website_checker(gallery.link)
					if check == valid_url:
						gallery.temp_url = gallery.link
						checked_pre_url_galleries.append(gallery)
						continue

				# dict -> hash:[list of title,url tuples] or None
				self.AUTO_METADATA_PROGRESS.emit("({}/{}) Finding url for gallery: {}".format(x, len(self.galleries), gallery.title))
				found_url = hen.eh_hash_search(gallery.hash)
				if found_url == 'error':
					gui_constants.GLOBAL_EHEN_LOCK = False
					self.FINISHED.emit(True)
					return
				if not gallery.hash in found_url:
					self.error_galleries.append(gallery)
					self.AUTO_METADATA_PROGRESS.emit("Could not find url for gallery: {}".format(gallery.title))
					log_w('Could not find url for gallery: {}'.format(gallery.title.encode(errors='ignore')))
					continue
				title_url_list = found_url[gallery.hash]
				if gui_constants.ALWAYS_CHOOSE_FIRST_HIT:
					title = title_url_list[0][0]
					url = title_url_list[0][1]
				else:
					if len(title_url_list) > 1:
						self.AUTO_METADATA_PROGRESS.emit("Multiple galleries found for gallery: {}".format(gallery.title))
						gui_constants.SYSTEM_TRAY.showMessage('Happypanda', 'Multiple galleries found for gallery:\n{}'.format(gallery.title),
											minimized=True)
						log_w("Multiple galleries found for gallery: {}".format(gallery.title.encode(errors='ignore')))
						self.GALLERY_PICKER.emit(gallery, title_url_list, self.GALLERY_PICKER_QUEUE)
						user_choice = self.GALLERY_PICKER_QUEUE.get()
					else:
						user_choice = title_url_list[0]

					title = user_choice[0]
					url = user_choice[1]

				if not gallery.link:
					gallery.link = url
					self.GALLERY_EMITTER.emit(gallery)
				gallery.temp_url = url
				self.AUTO_METADATA_PROGRESS.emit("({}/{}) Adding to queue: {}".format(
					x, len(self.galleries), gallery.title))
				if x == len(self.galleries):
					self.fetch_metadata(gallery, hen, True)
				else:
					self.fetch_metadata(gallery, hen)

			if checked_pre_url_galleries:
				for x, gallery in enumerate(checked_pre_url_galleries, 1):
					self.AUTO_METADATA_PROGRESS.emit("({}/{}) Adding to queue: {}".format(
						x, len(checked_pre_url_galleries), gallery.title))
					if x == len(checked_pre_url_galleries):
						self.fetch_metadata(gallery, hen, True)
					else:
						self.fetch_metadata(gallery, hen)

			log_d('Auto metadata fetcher is done')
			gui_constants.GLOBAL_EHEN_LOCK = False
			if not self.error_galleries:
				self.AUTO_METADATA_PROGRESS.emit('Done! Successfully fetched metadata for {} galleries.'.format(len(self.galleries)))
				gui_constants.SYSTEM_TRAY.showMessage('Done', 'Auto metadata fetcher is done!', minimized=True)
				self.FINISHED.emit(True)
			else:
				self.AUTO_METADATA_PROGRESS.emit('Done! Could not fetch metadata for  {} galleries. Check happypanda.log for more details!'.format(len(self.error_galleries)))
				gui_constants.SYSTEM_TRAY.showMessage('Done!',
										  'Could not fetch metadat for {} galleries. Check happypanda.log for more details!'.format(len(self.error_galleries)),
										  minimized=True)
				for e in error_galleries:
					log_e("An error occured with gallery: {}".format.title.encode(errors='ignore'))
				self.FINISHED.emit(False)
		else:
			log_e('Auto metadata fetcher is already running')
			self.AUTO_METADATA_PROGRESS.emit('Auto metadata fetcher is already running!')
			self.FINISHED.emit(False)

	def website_checker(self, url):
		if not url:
			return None
		try:
			r = regex.match('^(?=http)', url).group()
			del r
		except AttributeError:
			n_url = 'http://' + url

		if 'g.e-hentai.org' in url:
			return 'ehen'
		elif 'exhentai.org' in url:
			return 'exhen'
		else:
			log_e('Invalid URL')
			return None

