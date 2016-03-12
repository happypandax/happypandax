#"""
#This file is part of Happypanda.
#Happypanda is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 2 of the License, or
#any later version.
#Happypanda is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#You should have received a copy of the GNU General Public License
#along with Happypanda.  If not, see <http://www.gnu.org/licenses/>.
#"""

import os, time, logging, uuid, random, queue, scandir
import re as regex

from PyQt5.QtCore import QObject, pyqtSignal # need this for interaction with main thread

from gallerydb import Gallery, GalleryDB, HashDB, add_method_queue
import app_constants
import pewnet
import settings
import utils

"""This file contains functions to fetch gallery data"""

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical

class Fetch(QObject):
	"""
	A class containing methods to fetch gallery data.
	Should be executed in a new thread.
	Contains following methods:
	local -> runs a local search in the given series_path
	auto_web_metadata -> does a search online for the given galleries and returns their metdata
	"""

	# local signals
	FINISHED = pyqtSignal(object)
	DATA_COUNT = pyqtSignal(int)
	PROGRESS = pyqtSignal(int)
	SKIPPED = pyqtSignal(list)

	# WEB signals
	GALLERY_EMITTER = pyqtSignal(Gallery, object, object)
	AUTO_METADATA_PROGRESS = pyqtSignal(str)
	GALLERY_PICKER = pyqtSignal(object, list, queue.Queue)
	GALLERY_PICKER_QUEUE = queue.Queue()
	

	def __init__(self, parent=None):
		super().__init__(parent)
		self.series_path = ""
		self.data = []
		self._curr_gallery = '' # for debugging purposes
		self.skipped_paths = []

		# web
		self._default_ehen_url = app_constants.DEFAULT_EHEN_URL
		self.galleries = []
		self.galleries_in_queue = []
		self.error_galleries = []
		self._hen_list = []

		#filter
		self.galleries_from_db = []
		self._refresh_filter_list()

	def _refresh_filter_list(self):
			gallery_data = app_constants.GALLERY_DATA
			filter_list = []
			for g in gallery_data:
				filter_list.append(os.path.normcase(g.path))
			self.galleries_from_db = sorted(filter_list)

	def local(self, s_path=None):
		"""
		Do a local search in the given series_path.
		"""
		self.data.clear()
		if s_path:
			self.series_path = s_path
		try:
			gallery_l = sorted([p.name for p in scandir.scandir(self.series_path)]) #list of folders in the "Gallery" folder
			mixed = False
		except TypeError:
			gallery_l = self.series_path
			mixed = True
		if len(gallery_l) != 0: # if gallery path list is not empty
			log_i('Gallery folder is not empty')
			try:
				if len(self.galleries_from_db) != len(app_constants.GALLERY_DATA):
					self._refresh_filter_list()
				self.DATA_COUNT.emit(len(gallery_l)) #tell model how many items are going to be added
				log_i('Received {} paths'.format(len(gallery_l)))
				progress = 0
				def create_gallery(path, folder_name, do_chapters=True, archive=None):
					is_archive = True if archive else False
					temp_p = archive if is_archive else path
					folder_name = folder_name or path if folder_name or path else os.path.split(archive)[1]
					if utils.check_ignore_list(temp_p) and not GalleryDB.check_exists(temp_p, self.galleries_from_db, False):
						log_i('Creating gallery: {}'.format(folder_name.encode('utf-8', 'ignore')))
						if app_constants.MOVE_IMPORTED_GALLERIES and not app_constants.OVERRIDE_MOVE_IMPORTED_IN_FETCH:
							temp_p = utils.move_files(temp_p)
						new_gallery = Gallery()
						images_paths = []
						metafile = utils.GMetafile()
						try:
							con = scandir.scandir(temp_p) #all of content in the gallery folder
							log_i('Gallery source is a directory')
							chapters = sorted([sub.path for sub in con if sub.is_dir() or sub.name.endswith(utils.ARCHIVE_FILES)])\
							    if do_chapters else [] #subfolders
							# if gallery has chapters divided into sub folders
							numb_of_chapters = len(chapters)
							if numb_of_chapters != 0:
								log_i('Gallery has {} chapters'.format(numb_of_chapters))
								for ch in chapters:
									chap = new_gallery.chapters.create_chapter()
									chap.title = utils.title_parser(ch)['title']
									chap.path = os.path.join(path, ch)
									chap.pages = len([x for x in scandir.scandir(chap.path) if x.name.endswith(utils.IMG_FILES)])
									metafile.update(utils.GMetafile(chap.path))

							else: #else assume that all images are in gallery folder
								chap = new_gallery.chapters.create_chapter()
								chap.title = utils.title_parser(os.path.split(path)[1])['title']
								chap.path = path
								metafile.update(utils.GMetafile(chap.path))
								chap.pages = len(list(scandir.scandir(path)))
				
							parsed = utils.title_parser(folder_name)
						except NotADirectoryError:
							try:
								if is_archive or temp_p.endswith(utils.ARCHIVE_FILES):
									log_i('Gallery source is an archive')
									contents = utils.check_archive(temp_p)
									if contents:
										new_gallery.is_archive = 1
										new_gallery.path_in_archive = '' if not is_archive else path
										if folder_name.endswith('/'):
											folder_name = folder_name[:-1]
											fn = os.path.split(folder_name)
											folder_name = fn[1] or fn[2]
										folder_name = folder_name.replace('/','')
										if folder_name.endswith(utils.ARCHIVE_FILES):
											n = folder_name
											for ext in utils.ARCHIVE_FILES:
												n = n.replace(ext, '')
											parsed = utils.title_parser(n)
										else:
											parsed = utils.title_parser(folder_name)
												
										if do_chapters:
											archive_g = sorted(contents)
											if not archive_g:
												log_w('No chapters found for {}'.format(temp_p.encode(errors='ignore')))
												raise ValueError
											for g in archive_g:
												chap = new_gallery.chapters.create_chapter()
												chap.in_archive = 1
												chap.title = utils.title_parser(g)['title']
												chap.path = g
												metafile.update(utils.GMetafile(g, temp_p))
												arch = utils.ArchiveFile(temp_p)
												chap.pages = len([x for x in arch.dir_contents(g) if x.endswith(utils.IMG_FILES)])
												arch.close()
										else:
											chap = new_gallery.chapters.create_chapter()
											chap.title = utils.title_parser(os.path.split(path)[1])['title']
											chap.in_archive = 1
											chap.path = path
											metafile.update(utils.GMetafile(path, temp_p))
											arch = utils.ArchiveFile(temp_p)
											chap.pages = len(arch.dir_contents(''))
											arch.close()
									else:
										raise ValueError
								else:
									raise ValueError
							except ValueError:
								log_w('Skipped {} in local search'.format(path.encode(errors='ignore')))
								self.skipped_paths.append((temp_p, 'Empty archive',))
								return
							except app_constants.CreateArchiveFail:
								log_w('Skipped {} in local search'.format(path.encode(errors='ignore')))
								self.skipped_paths.append((temp_p, 'Error creating archive',))
								return

						new_gallery.title = parsed['title']
						new_gallery.path = temp_p
						new_gallery.artist = parsed['artist']
						new_gallery.language = parsed['language']
						new_gallery.info = ""
						metafile.apply_gallery(new_gallery)

						self.data.append(new_gallery)
						log_i('Gallery successful created: {}'.format(folder_name.encode('utf-8', 'ignore')))
					else:
						log_i('Gallery already exists or ignored: {}'.format(folder_name.encode('utf-8', 'ignore')))
						self.skipped_paths.append((temp_p, 'Already exists or ignored'))

				for folder_name in gallery_l: # folder_name = gallery folder title
					self._curr_gallery = folder_name
					if mixed:
						path = folder_name
						folder_name = os.path.split(path)[1]
					else:
						path = os.path.join(self.series_path, folder_name)
					if app_constants.SUBFOLDER_AS_GALLERY or app_constants.OVERRIDE_SUBFOLDER_AS_GALLERY:
						if app_constants.OVERRIDE_SUBFOLDER_AS_GALLERY:
							app_constants.OVERRIDE_SUBFOLDER_AS_GALLERY = False
						log_i("Treating each subfolder as gallery")
						if os.path.isdir(path):
							gallery_folders, gallery_archives = utils.recursive_gallery_check(path)
							for gs in gallery_folders:
									create_gallery(gs, os.path.split(gs)[1], False)
							p_saving = {}
							for gs in gallery_archives:
									
									create_gallery(gs[0], os.path.split(gs[0])[1], False, archive=gs[1])
						elif path.endswith(utils.ARCHIVE_FILES):
							for g in utils.check_archive(path):
								create_gallery(g, os.path.split(g)[1], False, archive=path)
					else:
						try:
							if os.path.isdir(path):
								if not list(scandir.scandir(path)):
									raise ValueError
							elif not path.endswith(utils.ARCHIVE_FILES):
								raise NotADirectoryError

							log_i("Treating each subfolder as chapter")
							create_gallery(path, folder_name, do_chapters=True)

						except ValueError:
							self.skipped_paths.append((path, 'Empty directory'))
							log_w('Directory is empty: {}'.format(path.encode(errors='ignore')))
						except NotADirectoryError:
							self.skipped_paths.append((path, 'Unsupported file'))
							log_w('Unsupported file: {}'.format(path.encode(errors='ignore')))

					progress += 1 # update the progress bar
					self.PROGRESS.emit(progress)
			except:
				log.exception('Local Search Error:')
				app_constants.OVERRIDE_MOVE_IMPORTED_IN_FETCH = True # sanity check
				self.FINISHED.emit(False)
		else: # if gallery folder is empty
			log_e('Local search error: Invalid directory')
			log_e('Gallery folder is empty')
			app_constants.OVERRIDE_MOVE_IMPORTED_IN_FETCH = True # sanity check
			self.FINISHED.emit(False)
			# might want to include an error message
		app_constants.OVERRIDE_MOVE_IMPORTED_IN_FETCH = False
		# everything went well
		log_i('Local search: OK')
		log_i('Created {} items'.format(len(self.data)))
		self.FINISHED.emit(self.data)
		if self.skipped_paths:
			self.SKIPPED.emit(self.skipped_paths)

	def _return_gallery_metadata(self, gallery):
		"Emits galleries"
		assert isinstance(gallery, Gallery)
		if gallery:
			gallery.exed = 1
			self.GALLERY_EMITTER.emit(gallery, None, False)
			log_d('Success')

	def fetch_metadata(self, gallery=None, hen=None, proc=False):
		"""
		Puts gallery in queue for metadata fetching. Applies received galleries and sends
		them to gallery model.
		Set proc to true if you want to process the queue immediately
		"""
		if gallery:
			log_i("Fetching metadata for gallery: {}".format(gallery.title.encode(errors='ignore')))
			log_i("Adding to queue: {}".format(gallery.title.encode(errors='ignore')))
			if proc:
				metadata = hen.add_to_queue(gallery.temp_url, True)
			else:
				metadata = hen.add_to_queue(gallery.temp_url)
			self.galleries_in_queue.append(gallery)
		else:
			metadata = hen.add_to_queue(proc=True)

		if metadata == 1: # Gallery is now put in queue
			return None
		# We received something from get_metadata
		if not metadata: # metadata fetching failed
			if gallery:
				self.error_galleries.append((gallery, "No metadata found for gallery"))
				log_i("An error occured while fetching metadata with gallery: {}".format(
					gallery.title.encode(errors='ignore')))
			return None
		self.AUTO_METADATA_PROGRESS.emit("Applying metadata...")

		for x, g in enumerate(self.galleries_in_queue, 1):
			try:
				data = metadata[g.temp_url]
			except KeyError:
				self.AUTO_METADATA_PROGRESS.emit("No metadata found for gallery: {}".format(g.title))
				self.error_galleries.append((g, "No metadata found for gallery"))
				log_w("No metadata found for gallery: {}".format(g.title.encode(errors='ignore')))
				continue
			log_i('({}/{}) Applying metadata for gallery: {}'.format(x, len(self.galleries_in_queue),
															g.title.encode(errors='ignore')))
			if app_constants.REPLACE_METADATA:
				g = hen.apply_metadata(g, data, False)
			else:
				g = hen.apply_metadata(g, data)
			self._return_gallery_metadata(g)
			log_i('Successfully applied metadata to gallery: {}'.format(g.title.encode(errors='ignore')))
		self.galleries_in_queue.clear()
		self.AUTO_METADATA_PROGRESS.emit('Finished applying metadata')
		log_i('Finished applying metadata')

	def _auto_metadata_process(self, galleries, hen, valid_url, **kwargs):
		hen.LAST_USED = time.time()
		self.AUTO_METADATA_PROGRESS.emit("Checking gallery urls...")

		fetched_galleries = []
		checked_pre_url_galleries = []
		multiple_hit_galleries = []
		for x, gallery in enumerate(galleries, 1):
			custom_args = {} # send to hen class
			log_i("Checking gallery url")

			# coming from GalleryDialog
			if hasattr(gallery, "_g_dialog_url"):
				if gallery._g_dialog_url:
					gallery.temp_url = gallery._g_dialog_url
					checked_pre_url_galleries.append(gallery)
					# to process even if this gallery is last and fails
					if x == len(galleries):
						self.fetch_metadata(hen=hen)
					continue

			if gallery.link and app_constants.USE_GALLERY_LINK:
				check = self._website_checker(gallery.link)
				if check == valid_url:
					gallery.temp_url = gallery.link
					checked_pre_url_galleries.append(gallery)
					if x == len(galleries):
						self.fetch_metadata(hen=hen)
					continue

			self.AUTO_METADATA_PROGRESS.emit("({}/{}) Generating gallery hash: {}".format(x, len(galleries), gallery.title))
			log_i("Generating gallery hash: {}".format(gallery.title.encode(errors='ignore')))
			hash = None
			try:
				if not gallery.hashes:
					color_img = kwargs['color'] if 'color' in kwargs else False # used for similarity search on EH
					hash_dict = add_method_queue(HashDB.gen_gallery_hash, False, gallery, 0, 'mid', color_img)
					if color_img and 'color' in hash_dict:
						custom_args['color'] = hash_dict['color'] # will be path to filename
						hash = hash_dict['color']
					elif hash_dict:
						hash = hash_dict['mid']
				else:
					hash = gallery.hashes[random.randint(0, len(gallery.hashes)-1)]
			except app_constants.CreateArchiveFail:
				pass
			if not hash:
				self.error_galleries.append((gallery, "Could not generate hash"))
				log_e("Could not generate hash for gallery: {}".format(gallery.title.encode(errors='ignore')))
				if x == len(galleries):
					self.fetch_metadata(hen=hen)
				continue
			gallery.hash = hash

			# dict -> hash:[list of title,url tuples] or None
			self.AUTO_METADATA_PROGRESS.emit("({}/{}) Finding url for gallery: {}".format(x, len(galleries), gallery.title))
			found_url = hen.search(gallery.hash, **custom_args)
			if found_url == 'error':
				app_constants.GLOBAL_EHEN_LOCK = False
				self.FINISHED.emit(True)
				return
			if not gallery.hash in found_url:
				self.error_galleries.append((gallery, "Could not find url for gallery"))
				self.AUTO_METADATA_PROGRESS.emit("Could not find url for gallery: {}".format(gallery.title))
				log_w('Could not find url for gallery: {}'.format(gallery.title.encode(errors='ignore')))
				if x == len(galleries):
					self.fetch_metadata(hen=hen)
				continue
			title_url_list = found_url[gallery.hash]

			if not len(title_url_list) > 1 or app_constants.ALWAYS_CHOOSE_FIRST_HIT:
				title = title_url_list[0][0]
				url = title_url_list[0][1]
			else:
				multiple_hit_galleries.append([gallery, title_url_list])
				if x == len(galleries):
					self.fetch_metadata(hen=hen)
				continue

			if not gallery.link:
				if isinstance(hen, (pewnet.EHen, pewnet.ExHen)):
					gallery.link = url
					self.GALLERY_EMITTER.emit(gallery, None, None)
			gallery.temp_url = url
			self.AUTO_METADATA_PROGRESS.emit("({}/{}) Adding to queue: {}".format(
				x, len(galleries), gallery.title))

			self.fetch_metadata(gallery, hen, x == len(galleries))

		if checked_pre_url_galleries:
			for x, gallery in enumerate(checked_pre_url_galleries, 1):
				self.AUTO_METADATA_PROGRESS.emit("({}/{}) Adding to queue: {}".format(
					x, len(checked_pre_url_galleries), gallery.title))
				self.fetch_metadata(gallery, hen, x == len(checked_pre_url_galleries))

		if multiple_hit_galleries:
			skip_all = False
			multiple_hit_g_queue = []
			for x, g_data in enumerate(multiple_hit_galleries, 1):
				gallery = g_data[0]
				log_w("Multiple galleries found for gallery: {}".format(gallery.title.encode(errors='ignore')))
				if skip_all:
					log_w("Skipping gallery")
					continue
				title_url_list = g_data[1]

				self.AUTO_METADATA_PROGRESS.emit("Multiple galleries found for gallery: {}".format(gallery.title))
				app_constants.SYSTEM_TRAY.showMessage('Happypanda', 'Multiple galleries found for gallery:\n{}'.format(gallery.title),
									minimized=True)
				self.GALLERY_PICKER.emit(gallery, title_url_list, self.GALLERY_PICKER_QUEUE)
				user_choice = self.GALLERY_PICKER_QUEUE.get()

				if user_choice == None:
					skip_all = True
				if not user_choice:
					log_w("Skipping gallery")
					continue

				title = user_choice[0]
				url = user_choice[1]

				if not gallery.link:
					gallery.link = url
					if isinstance(hen, (pewnet.EHen, pewnet.ExHen)):
						self.GALLERY_EMITTER.emit(gallery, None, None)
				gallery.temp_url = url
				self.AUTO_METADATA_PROGRESS.emit("({}/{}) Adding to queue: {}".format(
					x, len(multiple_hit_galleries), gallery.title))
				multiple_hit_g_queue.append(gallery)

			for x, g in enumerate(multiple_hit_g_queue, 1):
				self.fetch_metadata(g, hen, x == len(multiple_hit_g_queue))


	def _website_checker(self, url):
		if not url:
			return None
		if 'g.e-hentai.org/g/' in url:
			return 'ehen'
		elif 'exhentai.org/g/' in url:
			return 'exhen'
		elif 'panda.chaika.moe/archive/' in url or 'panda.chaika.moe/gallery/' in url:
			return 'chaikahen'
		else:
			log_e('Invalid URL')
			return None

	def auto_web_metadata(self):
		"""
		Auto fetches metadata for the provided list of galleries.
		Appends or replaces metadata with the new fetched metadata.
		"""
		log_i('Initiating auto metadata fetcher')
		self._hen_list = pewnet.hen_list_init()
		if self.galleries and not app_constants.GLOBAL_EHEN_LOCK:
			log_i('Auto metadata fetcher is now running')
			app_constants.GLOBAL_EHEN_LOCK = True

			def fetch_cancelled(rsn=''):
				if rsn:
					self.AUTO_METADATA_PROGRESS.emit("Metadata fetching cancelled: {}".format(rsn))
					app_constants.SYSTEM_TRAY.showMessage("Metadata", "Metadata fetching cancelled: {}".format(rsn), minimized=True)
				else:
					self.AUTO_METADATA_PROGRESS.emit("Metadata fetching cancelled!")
					app_constants.SYSTEM_TRAY.showMessage("Metadata", "Metadata fetching cancelled!", minimized=True)
				app_constants.GLOBAL_EHEN_LOCK = False
				self.FINISHED.emit(False)

			if 'exhentai' in self._default_ehen_url:
				try:
					exprops = settings.ExProperties()
					if exprops.check():
						hen = pewnet.ExHen(exprops.cookies)
						valid_url = 'exhen'
						log_i("using exhen")
					else:
						raise ValueError
				except ValueError:
					hen = pewnet.EHen()
					valid_url = 'ehen'
					log_i("using ehen")
			else:
				hen = pewnet.EHen()
				valid_url = 'ehen'
				log_i("Using Exhentai")
			try:
				self._auto_metadata_process(self.galleries, hen, valid_url, color=True)
			except app_constants.MetadataFetchFail as err:
				fetch_cancelled(err)
				return

			if self.error_galleries:
				if self._hen_list:
					log_i("Using fallback source")
					self.AUTO_METADATA_PROGRESS.emit("Using fallback source")
					for hen in self._hen_list:
						if not self.error_galleries:
							break
						galleries = [x[0] for x in self.error_galleries]
						self.error_galleries.clear()
						
						valid_url = ""

						if hen == pewnet.ChaikaHen:
							valid_url = "chaikahen"
							log_i("using chaika hen")
						try:
							self._auto_metadata_process(galleries, hen(), valid_url)
						except app_constants.MetadataFetchFail as err:
							fetch_cancelled(err)
							return

			if not self.error_galleries:
				self.AUTO_METADATA_PROGRESS.emit('Successfully fetched metadata! Went through {} galleries successfully!'.format(len(self.galleries)))
				app_constants.SYSTEM_TRAY.showMessage('Successfully fetched metadata', 'Went through {} galleries successfully!'.format(len(self.galleries)), minimized=True)
				self.FINISHED.emit(True)
			else:
				self.AUTO_METADATA_PROGRESS.emit('Finished fetching metadata! Could not fetch metadata for {} galleries. Check happypanda.log for more details!'.format(len(self.error_galleries)))
				app_constants.SYSTEM_TRAY.showMessage('Finished fetching metadata',
											'Could not fetch metadata for {} galleries. Check happypanda.log for more details!'.format(len(self.error_galleries)),
											minimized=True)
				for tup in self.error_galleries:
					log_e("{}: {}".format(tup[1], tup[0].title.encode(errors='ignore')))
				self.FINISHED.emit(self.error_galleries)
			log_i('Auto metadata fetcher is done')
			app_constants.GLOBAL_EHEN_LOCK = False
		else:
			log_e('Auto metadata fetcher is already running')
			self.AUTO_METADATA_PROGRESS.emit('Auto metadata fetcher is already running!')
			self.FINISHED.emit(False)

