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

import datetime, os, scandir, threading, logging, queue, uuid # for unique filename
import re as regex

from PyQt5.QtCore import Qt, QObject, pyqtSignal
from PyQt5.QtGui import QImage

from utils import (today, ArchiveFile, generate_img_hash, delete_path,
					 ARCHIVE_FILES, get_gallery_img, IMG_FILES)
from database import db_constants
from database.db import DBBase

import gui_constants
import utils

PROFILE_TO_MODEL = queue.Queue()
TestQueue = queue.Queue()

log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical

method_queue = queue.Queue()
method_return = queue.Queue()
db_constants.METHOD_QUEUE = method_queue
db_constants.METHOD_RETURN = method_return
def process_methods():
	"""
	Methods are objects.
	Put a list in the method queue where first index is the
	method. Named arguments are put in a dict.
	"""
	while True:
		print('waiting for method')
		l = method_queue.get()
		log_d('Processing a method from queue...')
		method = l.pop(0)
		log_d(method)
		args = []
		kwargs = {}
		get_args = 1
		no_return = False
		while get_args:
			try:
				a = l.pop(0)
				if a == 'no return':
					no_return = True
					continue
				if isinstance(a, dict):
					kwargs = a
				else:
					args.append(a)
			except IndexError:
				get_args = 0
		args = tuple(args)
		print('calling')
		if args and kwargs:
			r = method(*args, **kwargs)
		elif args:
			r = method(*args)
		elif kwargs:
			r = method(**kwargs)
		else:
			r = method()
		print('called method')
		if not no_return:
			method_return.put(r)
		method_queue.task_done()

method_queue_thread = threading.Thread(name='Method Queue Thread', target=process_methods,
									   daemon=True)
method_queue_thread.start()

def add_method_queue(method, no_return, *args, **kwargs):
	log_d('Added method to queue')
	log_d('Method name: {}'.format(method.__name__))
	arg_list = [method]
	if no_return:
		arg_list.append('no return')
	if args:
		for x in args:
			arg_list.append(x)
	if kwargs:
		arg_list.append(kwargs)
	method_queue.put(arg_list)
	print('putted method to queue')
	if not no_return:
		return method_return.get()

def gen_thumbnail(gallery, width=gui_constants.THUMB_W_SIZE,
				height=gui_constants.THUMB_H_SIZE, img=None):
	"""Generates a thumbnail with unique filename in the cache dir.
	Returns absolute path to the created thumbnail
	"""
	assert isinstance(gallery, Gallery), "gallery should be an instance of Gallery class"

	img_path_queue = queue.Queue()
	# generate a cache dir if required
	if not os.path.isdir(db_constants.THUMBNAIL_PATH):
		os.mkdir(db_constants.THUMBNAIL_PATH)

	try:
		if not img:
			if gallery.is_archive:
				img_path = get_gallery_img(gallery.chapters[0].path, gallery.path)
			else:
				img_path = get_gallery_img(gallery.chapters[0].path)
		else:
			img_path = img
		if not img_path:
			raise IndexError
		for ext in IMG_FILES:
			if img_path.lower().endswith(ext):
				suff = ext # the image ext with dot

		# generate unique file name
		file_name = str(uuid.uuid4()) + suff
		new_img_path = os.path.join(db_constants.THUMBNAIL_PATH, (file_name))
		if not os.path.isfile(img_path):
			raise IndexError
		# Do the scaling
		image = QImage()
		image.load(img_path)
		if image.isNull():
			raise IndexError
		image = image.scaled(width, height, Qt.KeepAspectRatio, Qt.SmoothTransformation)
		image.save(new_img_path, quality=100)
	except IndexError:
		new_img_path = gui_constants.NO_IMAGE_PATH

	abs_path = os.path.abspath(new_img_path)
	return abs_path

def chapter_map(row, chapter):
	assert isinstance(chapter, Chapter)
	chapter.path = bytes.decode(row['chapter_path'])
	chapter.pages = row['pages']
	chapter.in_archive = row['in_archive']
	return chapter

def gallery_map(row, gallery):
	gallery.title = row['title']
	gallery.artist = row['artist']
	gallery.profile = bytes.decode(row['profile'])
	gallery.path = bytes.decode(row['series_path'])
	gallery.is_archive = row['is_archive']
	try:
		gallery.path_in_archive = bytes.decode(row['path_in_archive'])
	except TypeError:
		pass
	gallery.info = row['info']
	gallery.language = row['language']
	gallery.status = row['status']
	gallery.type = row['type']
	gallery.fav = row['fav']

	def convert_date(date_str):
		#2015-10-25 21:44:38
		if date_str and date_str != 'None':
			return datetime.datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")

	gallery.pub_date = convert_date(row['pub_date'])
	gallery.last_update = row['last_update']
	gallery.last_read = convert_date(row['last_read'])
	gallery.date_added = convert_date(row['date_added'])
	gallery.times_read = row['times_read']
	gallery._db_v = row['db_v']
	gallery.exed = row['exed']
	try:
		gallery.link = bytes.decode(row['link'])
	except TypeError:
		gallery.link = row['link']

	gallery.chapters = ChapterDB.get_chapters_for_gallery(gallery.id)

	gallery.tags = TagDB.get_gallery_tags(gallery.id)

	gallery.hashes = HashDB.get_gallery_hashes(gallery.id)

	return gallery

def default_chap_exec(gallery_or_id, chap, only_values=False):
	"Pass a Gallery object or gallery id and a Chapter object"
	if isinstance(gallery_or_id, Gallery):
		gid = gallery_or_id.id
		in_archive = gallery_or_id.is_archive
	else:
		gid = gallery_or_id
		in_archive = chap.in_archive

	if only_values:
		execute = (gid, chap.number, str.encode(chap.path), in_archive, chap.pages,)
	else:
		execute = ("""
				INSERT INTO chapters(series_id, chapter_number, chapter_path, pages, in_archive)
				VALUES(:series_id, :chapter_number, :chapter_path, :pages, :in_archive)""",
				{'series_id':gid,
				'chapter_number':chap.number,
				'chapter_path':str.encode(chap.path),
				'pages':chap.pages,
				'in_archive':in_archive}
				)
	return execute

def default_exec(object):
	def check(obj):
		if obj == None:
			return "None"
		else:
			return obj
	executing = ["""INSERT INTO series(title, artist, profile, series_path, is_archive,
					info, type, fav, status, pub_date, date_added, last_read, link, last_update,
					times_read, exed)
				VALUES(:title, :artist, :profile, :series_path, :is_archive, :info, :type, :fav,
					:status, :pub_date, :date_added, :last_read, :link, :last_update,
					:times_read, :exed)""",
				{
				'title':check(object.title),
				'artist':check(object.artist),
				'profile':str.encode(object.profile),
				'series_path':str.encode(object.path),
				'is_archive':check(object.is_archive),
				'path_in_archive':str.encode(object.path_in_archive),
				'info':check(object.info),
				'fav':check(object.fav),
				'type':check(object.type),
				'language':check(object.language),
				'status':check(object.status),
				'pub_date':check(object.pub_date),
				'date_added':check(object.date_added),
				'last_read':check(object.last_read),
				'last_update':check(object.last_update),
				'link':str.encode(object.link),
				'times_read':check(object.times_read),
				'db_v':check(db_constants.REAL_DB_VERSION),
				'exed':check(object.exed)
				}
				]
	return executing

class GalleryDB(DBBase):
	"""
	Provides the following s methods:
		rebuild_thumb -> Rebuilds gallery thumbnail
		rebuild_galleries -> Rebuilds the galleries in DB
		modify_gallery -> Modifies gallery with given gallery id
		fav_gallery_set -> Set fav on gallery with given gallery id, and returns the gallery
		get_all_gallery -> returns a list of all gallery (<Gallery> class) currently in DB
		get_gallery_by_path -> Returns gallery with given path
		get_gallery_by_id -> Returns gallery with given id
		add_gallery -> adds gallery into db
		add_gallery_return -> adds gallery into db AND returns the added gallery
		set_gallery_title -> changes gallery title
		gallery_count -> returns amount of gallery (can be used for indexing)
		del_gallery -> deletes the gallery with the given id recursively
		check_exists -> Checks if provided string exists
		clear_thumb -> Deletes a thumbnail
		clear_thumb_dir -> Dletes everything in the thumbnail directory
	"""
	def __init__(self):
		raise Exception("GalleryDB should not be instantiated")

	@staticmethod
	def rebuild_thumb(gallery):
		"Rebuilds gallery thumbnail"
		try:
			log_i('Recreating thumb {}'.format(gallery.title.encode(errors='ignore')))
			if gallery.profile:
				GalleryDB.clear_thumb(gallery.profile)
			gallery.profile = gen_thumbnail(gallery)
			GalleryDB.modify_gallery(
				gallery.id,
				profile=gallery.profile)
		except:
			log.exception("Failed rebuilding thumbnail")
			return False
		return True

	@staticmethod
	def clear_thumb(path):
		"Deletes a thumbnail"
		try:
			if path != gui_constants.NO_IMAGE_PATH:
				os.unlink(path)
		except:
			log.exception('Failed to delete thumb {}'.format(os.path.split(path)[1].encode(errors='ignore')))

	@staticmethod
	def clear_thumb_dir():
		"Deletes everything in the thumbnail directory"
		for thumbfile in scandir.scandir(db_constants.THUMBNAIL_PATH):
			GalleryDB.clear_thumb(thumbfile.path)

	@staticmethod
	def rebuild_gallery(gallery, thumb=False):
		"Rebuilds the galleries in DB"
		try:
			log_i('Rebuilding {}'.format(gallery.title.encode(errors='ignore')))
			log_i("Rebuilding gallery {}".format(gallery.id))
			HashDB.del_gallery_hashes(gallery.id)
			GalleryDB.modify_gallery(
				gallery.id,
				title=gallery.title,
				artist=gallery.artist,
				info=gallery.info,
				type=gallery.type,
				fav=gallery.fav,
				tags=gallery.tags,
				language=gallery.language,
				status=gallery.status,
				pub_date=gallery.pub_date,
				link=gallery.link,
				times_read=gallery.times_read,
				_db_v=db_constants.CURRENT_DB_VERSION,
				exed=gallery.exed,
				is_archive=gallery.is_archive,
				path_in_archive=gallery.path_in_archive)
			if thumb:
				GalleryDB.rebuild_thumb(gallery)
		except:
			log.exception('Failed rebuilding')
			return False
		return True

	@classmethod
	def modify_gallery(cls, series_id, title=None, profile=None, artist=None, info=None, type=None, fav=None,
				   tags=None, language=None, status=None, pub_date=None, link=None,
				   times_read=None, series_path=None, chapters=None, _db_v=None,
				   hashes=None, exed=None, is_archive=None, path_in_archive=None):
		"Modifies gallery with given gallery id"
		assert isinstance(series_id, int)
		executing = []
		if title != None:
			assert isinstance(title, str)
			executing.append(["UPDATE series SET title=? WHERE series_id=?", (title, series_id)])
		if profile != None:
			assert isinstance(profile, str)
			executing.append(["UPDATE series SET profile=? WHERE series_id=?", (str.encode(profile), series_id)])
		if artist != None:
			assert isinstance(artist, str)
			executing.append(["UPDATE series SET artist=? WHERE series_id=?", (artist, series_id)])
		if info != None:
			assert isinstance(info, str)
			executing.append(["UPDATE series SET info=? WHERE series_id=?", (info, series_id)])
		if type != None:
			assert isinstance(type, str)
			executing.append(["UPDATE series SET type=? WHERE series_id=?", (type, series_id)])
		if fav != None:
			assert isinstance(fav, int)
			executing.append(["UPDATE series SET fav=? WHERE series_id=?", (fav, series_id)])
		if language != None:
			assert isinstance(language, str)
			executing.append(["UPDATE series SET language=? WHERE series_id=?", (language, series_id)])
		if status != None:
			assert isinstance(status, str)
			executing.append(["UPDATE series SET status=? WHERE series_id=?", (status, series_id)])
		if pub_date != None:
			executing.append(["UPDATE series SET pub_date=? WHERE series_id=?", (pub_date, series_id)])
		if link != None:
			executing.append(["UPDATE series SET link=? WHERE series_id=?", (link, series_id)])
		if times_read != None:
			executing.append(["UPDATE series SET times_read=? WHERE series_id=?", (times_read, series_id)])
		if series_path != None:
			executing.append(["UPDATE series SET series_path=? WHERE series_id=?", (str.encode(series_path), series_id)])
		if _db_v != None:
			executing.append(["UPDATE series SET db_v=? WHERE series_id=?", (_db_v, series_id)])
		if exed != None:
			executing.append(["UPDATE series SET exed=? WHERE series_id=?", (exed, series_id)])
		if is_archive != None:
			executing.append(["UPDATE series SET is_archive=? WHERE series_id=?", (is_archive, series_id)])
		if path_in_archive != None:
			executing.append(["UPDATE series SET path_in_archive=? WHERE series_id=?", (path_in_archive, series_id)])

		if tags != None:
			assert isinstance(tags, dict)
			TagDB.modify_tags(series_id, tags)
		if chapters != None:
			assert isinstance(chapters, ChaptersContainer)
			ChapterDB.update_chapter(chapters)

		if hashes != None:
			assert isinstance(hashes, Gallery)
			HashDB.rebuild_gallery_hashes(hashes)

		for query in executing:
			cls.execute(cls, *query)

	@classmethod
	def get_all_gallery(cls):
		"""
		Careful, might crash with very large libraries i think...
		Returns a list of all galleries (<Gallery> class) currently in DB
		"""
		cursor = cls.execute(cls, 'SELECT * FROM series')
		all_gallery = cursor.fetchall()
		return GalleryDB.gen_galleries(all_gallery)

	@staticmethod
	def gen_galleries(gallery_dict):
		"""
		Map galleries fetched from DB
		"""
		gallery_list = []
		for gallery_row in gallery_dict:
			gallery = Gallery()
			gallery.id = gallery_row['series_id']
			gallery = gallery_map(gallery_row, gallery)
			gallery.validate()
			gallery_list.append(gallery)

		return gallery_list

	@classmethod
	def get_gallery_by_path(cls, path):
		"Returns gallery with given path"
		assert isinstance(path, str), "Provided path is invalid"
		cursor = cls.execute(cls, 'SELECT * FROM series WHERE series_path=?', (path,))
		row = cursor.fetchone()
		gallery = Gallery()
		try:
			gallery.id = row['series_id']
			gallery = gallery_map(row, gallery)
			return gallery
		except TypeError:
			return None

	@classmethod
	def get_gallery_by_id(cls, id):
		"Returns gallery with given id"
		assert isinstance(id, int), "Provided ID is invalid"
		cursor = cls.execute(cls, 'SELECT * FROM series WHERE series_id=?', (id,))
		row = cursor.fetchone()
		gallery = Gallery()
		try:
			gallery.id = row['series_id']
			gallery = gallery_map(row, gallery)
			return gallery
		except TypeError:
			return None

	@classmethod
	def add_gallery(cls, object, test_mode=False):
		"Receives an object of class gallery, and appends it to DB"
		"Adds gallery of <Gallery> class into database"
		assert isinstance(object, Gallery), "add_gallery method only accepts gallery items"
		log_i('Recevied gallery: {}'.format(object.path.encode(errors='ignore')))

		object.profile = gen_thumbnail(object)

		cursor = cls.execute(cls, *default_exec(object))
		series_id = cursor.lastrowid
		object.id = series_id
		if object.tags:
			TagDB.add_tags(object)
		ChapterDB.add_chapters(object)

	@classmethod
	def add_gallery_return(cls, object):
		"""Adds gallery of <Gallery> class into database AND returns the profile generated"""
		assert isinstance(object, Gallery), "[add_gallery_return] method only accept gallery items"
		log_i('Recevied gallery: {}'.format(object.path.encode(errors='ignore')))

		object.profile = gen_thumbnail(object)
		PROFILE_TO_MODEL.put(object.profile)

		cursor = cls.execute(cls, *default_exec(object))
		series_id = cursor.lastrowid
		object.id = series_id
		if object.tags:
			TagDB.add_tags(object)
		ChapterDB.add_chapters(object)
		return GalleryDB.get_gallery_by_id(object.id)

	@classmethod
	def gallery_count(cls):
		"""
		Returns the amount of galleries in db.
		"""
		cursor = cls.execute(cls, "SELECT count(*) AS 'size' FROM series")
		return cursor.fetchone()['size']

	@classmethod
	def del_gallery(cls, list_of_gallery, local=False):
		"Deletes all galleries in the list recursively."
		assert isinstance(list_of_gallery, list), "Please provide a valid list of galleries to delete"
		for gallery in list_of_gallery:
			if local:
				if gallery.is_archive:
					s = delete_path(gallery.path)
				else:
					for chap in gallery.chapters:
						path = chap.path
						s = delete_path(path)
						if not s:
							log_e('Failed to delete chapter {}:{}, {}'.format(chap,
															gallery.id, gallery.title.encode('utf-8', 'ignore')))
							continue
					s = delete_path(gallery.path)

				if not s:
					log_e('Failed to delete gallery:{}, {}'.format(gallery.id,
													  gallery.title.encode('utf-8', 'ignore')))
					continue

			if gallery.profile != os.path.abspath(gui_constants.NO_IMAGE_PATH):
				try:
					os.remove(gallery.profile)
				except FileNotFoundError:
					pass
			cls.execute(cls, 'DELETE FROM series WHERE series_id=?', (gallery.id,))
			ChapterDB.del_all_chapters(gallery.id)
			TagDB.del_gallery_mapping(gallery.id)
			HashDB.del_gallery_hashes(gallery.id)
			log_i('Successfully deleted: {}'.format(gallery.title.encode('utf-8', 'ignore')))
			gui_constants.NOTIF_BAR.add_text('Successfully deleted: {}'.format(gallery.title))

	@staticmethod
	def check_exists(name, galleries=None, filter=True):
		"""
		Checks if provided string exists in provided sorted
		list based on path name.
		Note: key will be normcased
		"""
		#pdb.set_trace()
		if not galleries:
			galleries = gui_constants.GALLERY_DATA

		if filter:
			filter_list = []
			for gallery in galleries:
				filter_list.append(os.path.normcase(gallery.path))
			filter_list = sorted(filter_list)
		else:
			filter_list = galleries

		def binary_search(key):
			low = 0
			high = len(filter_list) - 1
			while high >= low:
				mid = low + (high - low) // 2
				if filter_list[mid] < key:
					low = mid + 1
				elif filter_list[mid] > key:
					high = mid - 1
				else:
					return True
			return False

		return binary_search(os.path.normcase(name))

class ChapterDB(DBBase):
	"""
	Provides the following database methods:
		update_chapter -> Updates an existing chapter in DB
		add_chapter -> adds chapter into db
		add_chapter_raw -> links chapter to the given seires id, and adds into db
		get_chapters_for_gallery -> returns a dict with chapters linked to the given series_id
		get_chapter-> returns a dict with chapter matching the given chapter_number
		get_chapter_id -> returns id of the chapter number
		chapter_size -> returns amount of manga (can be used for indexing)
		del_all_chapters <- Deletes all chapters with the given series_id
		del_chapter <- Deletes chapter with the given number from gallery
	"""

	def __init__(self):
		raise Exception("ChapterDB should not be instantiated")

	@classmethod
	def update_chapter(cls, chapter_container, numbers=[]):
		"""
		Updates an existing chapter in DB.
		Pass a gallery's ChapterContainer, specify number with a list of ints
		leave empty to update all chapters.
		"""
		assert isinstance(chapter_container, ChaptersContainer) and isinstance(numbers, (list, tuple))
		if numbers:
			chapters = []
			for n in numbers:
				chapters.append(chapter_container[n])
		else:
			chapters = chapter_container.get_all_chapters()

		executing = []
		for chap in chapters:
			new_path = chap.path
			executing.append((str.encode(new_path), chap.in_archive, chap.gallery.id, chap.number,))

		cls.executemany(cls, "UPDATE chapters SET chapter_path=?, in_archive=? WHERE series_id=? AND chapter_number=?",
			executing)

	@classmethod
	def add_chapters(cls, gallery_object):
		"Adds chapters linked to gallery into database"
		assert isinstance(gallery_object, Gallery), "Parent gallery need to be of class Gallery"
		series_id = gallery_object.id
		executing = []
		for chap in gallery_object.chapters:
			executing.append(default_chap_exec(gallery_object, chap, True))
		if not executing:
			raise Exception
		cls.executemany(cls, 'INSERT INTO chapters VALUES(NULL, ?, ?, ?, ?, ?)', executing)

	@classmethod
	def add_chapters_raw(cls, series_id, chapters_container):
		"Adds chapter(s) to a gallery with the received series_id"
		assert isinstance(chapters_container, ChaptersContainer), "chapters_container must be of class ChaptersContainer"
		executing = []
		executing2 = []
		for chap in chapters_container:
			if not ChapterDB.get_chapter(series_id, chap.number):
				executing.append(default_chap_exec(series_id, chap, True))
			else:
				cls.update_chapter(cls, chapters_container, [chap.number])

		cls.executemany(cls, 'INSERT INTO chapters VALUES(NULL, ?, ?, ?, ?, ?)', executing)


	@classmethod
	def get_chapters_for_gallery(cls, series_id):
		"""
		Returns a ChaptersContainer of chapters matching the received series_id
		"""
		assert isinstance(series_id, int), "Please provide a valid gallery ID"
		cursor = cls.execute(cls, 'SELECT * FROM chapters WHERE series_id=?', (series_id,))
		rows = cursor.fetchall()
		chapters = ChaptersContainer()
		for row in rows:
			chap = chapters.create_chapter(row['chapter_number'])
			chapter_map(row, chap)
		return chapters


	@classmethod
	def get_chapter(cls, series_id, chap_numb):
		"""Returns a ChaptersContainer of chapters matching the recieved chapter_number
		return None for no match
		"""
		assert isinstance(chap_numb, int), "Please provide a valid chapter number"
		cls.execute(cls, 'SELECT * FROM chapters WHERE series_id=? AND chapter_number=?', (series_id, chap_numb,))
		try:
			rows = cursor.fetchall()
			chapters = ChaptersContainer()
			for row in rows:
				chap = chapters.create_chapter(row['chapter_number'])
				chapter_map(row, chap)
		except TypeError:
			return None
		return chapters

	@classmethod
	def get_chapter_id(cls, series_id, chapter_number):
		"Returns id of the chapter number"
		assert isinstance(series_id, int) and isinstance(chapter_number, int),\
			"Passed args must be of int not {} and {}".format(type(series_id), type(chapter_number))
		cursor = cls.execute(cls, 'SELECT chapter_id FROM chapters WHERE series_id=? AND chapter_number=?',
						(series_id, chapter_number,))
		try:
			row = cursor.fetchone()
			chp_id = row['chapter_id']
			return chp_id
		except KeyError:
			return None
		except TypeError:
			return None

	@staticmethod
	def chapter_size(gallery_id):
		"""Returns the amount of chapters for the given
		gallery id
		"""
		pass

	@classmethod
	def del_all_chapters(cls, series_id):
		"Deletes all chapters with the given series_id"
		assert isinstance(series_id, int), "Please provide a valid gallery ID"
		cls.execute(cls, 'DELETE FROM chapters WHERE series_id=?', (series_id,))

	@classmethod
	def del_chapter(cls, series_id, chap_number):
		"Deletes chapter with the given number from gallery"
		assert isinstance(series_id, int), "Please provide a valid gallery ID"
		assert isinstance(chap_number, int), "Please provide a valid chapter number"
		cls.execute(cls, 'DELETE FROM chapters WHERE series_id=? AND chapter_number=?',
				(series_id, chap_number,))

class TagDB(DBBase):
	"""
	Tags are returned in a dict where {"namespace":["tag1","tag2"]}
	The namespace "default" will be used for tags without namespaces.

	Provides the following methods:
	del_tags <- Deletes the tags with corresponding tag_ids from DB
	del_gallery_tags_mapping <- Deletes the tags and gallery mappings with corresponding series_ids from DB
	get_gallery_tags -> Returns all tags and namespaces found for the given series_id;
	get_tag_gallery -> Returns all galleries with the given tag
	get_ns_tags -> "Returns a dict with namespace as key and list of tags as value"
	get_ns_tags_to_gallery -> Returns all galleries linked to the namespace tags. Receives a dict like this: {"namespace":["tag1","tag2"]}
	get_tags_from_namespace -> Returns all galleries linked to the namespace
	add_tags <- Adds the given dict_of_tags to the given series_id
	modify_tags <- Modifies the given tags
	get_all_tags -> Returns all tags in database
	get_all_ns -> Returns all namespaces in database
	"""

	def __init__(self):
		raise Exception("TagsDB should not be instantiated")

	@staticmethod
	def del_tags(list_of_tags_id):
		"Deletes the tags with corresponding tag_ids from DB"
		pass

	@classmethod
	def del_gallery_mapping(cls, series_id):
		"Deletes the tags and gallery mappings with corresponding series_ids from DB"
		assert isinstance(series_id, int), "Please provide a valid gallery id"
		# We first get all the current tags_mappings_ids related to gallery
		tag_m_ids = []
		c = cls.execute(cls, 'SELECT tags_mappings_id FROM series_tags_map WHERE series_id=?',
				(series_id,))
		for tmd in c.fetchall():
			tag_m_ids.append(tmd['tags_mappings_id'])

		# Then we delete all mappings related to the given series_id
		cls.execute(cls, 'DELETE FROM series_tags_map WHERE series_id=?', (series_id,))

		executing = []
		for tmd_id in tag_m_ids:
			executing.append((tmd_id,))

		cls.executemany(cls, 'DELETE FROM tags_mappings WHERE tags_mappings_id=?', executing)

	@classmethod
	def get_gallery_tags(cls, series_id):
		"Returns all tags and namespaces found for the given series_id"
		assert isinstance(series_id, int), "Please provide a valid gallery ID"
		cursor = cls.execute(cls, 'SELECT tags_mappings_id FROM series_tags_map WHERE series_id=?',
				(series_id,))
		tags = {}
		result = cursor.fetchall()
		for tag_map_row in result: # iterate all tag_mappings_ids
			try:
				if not tag_map_row:
					continue
				# get tag and namespace
				c = cls.execute(cls, 'SELECT namespace_id, tag_id FROM tags_mappings WHERE tags_mappings_id=?',
				  (tag_map_row['tags_mappings_id'],))
				for row in c.fetchall(): # iterate all rows
					# get namespace
					c = cls.execute(cls, 'SELECT namespace FROM namespaces WHERE namespace_id=?',
						(row['namespace_id'],))
					namespace = c.fetchone()['namespace']

					# get tag
					c = cls.execute(cls, 'SELECT tag FROM tags WHERE tag_id=?', (row['tag_id'],))
					try:
						tag = c.fetchone()['tag']
					except TypeError:
						continue

					# add them to dict
					if not namespace in tags:
						tags[namespace] = [tag]
					else:
						# namespace already exists in dict
						tags[namespace].append(tag)
			except IndexError:
				continue
		return tags

	@classmethod
	def add_tags(cls, object):
		"Adds the given dict_of_tags to the given series_id"
		assert isinstance(object, Gallery), "Please provide a valid gallery of class gallery"

		series_id = object.id
		dict_of_tags = object.tags

		def look_exists(tag_or_ns, what):
			"""check if tag or namespace already exists in base
			returns id, else returns None"""
			c = cls.execute(cls, 'SELECT {}_id FROM {}s WHERE {} = ?'.format(what, what, what),
				(tag_or_ns,))
			try: # exists
				return c.fetchone()['{}_id'.format(what)]
			except TypeError: # doesnt exist
				return None
			except IndexError:
				return None

		tags_mappings_id_list = []
		# first let's add the tags and namespaces to db
		for namespace in dict_of_tags:
			tags_list = dict_of_tags[namespace]
			# don't add if it already exists
			try:
				namespace_id = look_exists(namespace, "namespace")
				if not namespace_id:
					raise ValueError
			except ValueError:
				c = cls.execute(cls, 'INSERT INTO namespaces(namespace) VALUES(?)', (namespace,))
				namespace_id = c.lastrowid

			tags_id_list = []
			for tag in tags_list:
				try:
					tag_id = look_exists(tag, "tag")
					if not tag_id:
						raise ValueError
				except ValueError:
					c = cls.execute(cls, 'INSERT INTO tags(tag) VALUES(?)', (tag,))
					tag_id = c.lastrowid

				tags_id_list.append(tag_id)


			def look_exist_tag_map(tag_id):
				"Checks DB if the tag_id already exists with the namespace_id, returns id else None"
				c = cls.execute(cls, 'SELECT tags_mappings_id FROM tags_mappings WHERE namespace_id=? AND tag_id=?',
					(namespace_id, tag_id,))
				try: # exists
					return c.fetchone()['tags_mappings_id']
				except TypeError: # doesnt exist
					return None
				except IndexError:
					return None

			# time to map the tags to the namespace now
			for tag_id in tags_id_list:
				# First check if tags mappings exists
				try:
					t_map_id = look_exist_tag_map(tag_id)
					if t_map_id:
						tags_mappings_id_list.append(t_map_id)
					else:
						raise TypeError
				except TypeError:
					c = cls.execute(cls, 'INSERT INTO tags_mappings(namespace_id, tag_id) VALUES(?, ?)',
					 (namespace_id, tag_id,))
					# add the tags_mappings_id to our list
					tags_mappings_id_list.append(c.lastrowid)

		# Lastly we map the series_id to the tags_mappings
		executing = []
		for tags_map in tags_mappings_id_list:
				executing.append((series_id, tags_map,))
		cls.executemany(cls, 'INSERT INTO series_tags_map(series_id, tags_mappings_id) VALUES(?, ?)', executing)

	@staticmethod
	def modify_tags(series_id, dict_of_tags):
		"Modifies the given tags"

		# We first delete all mappings
		TagDB.del_gallery_mapping(series_id)

		# Now we add the new tags to DB
		weak_gallery = Gallery()
		weak_gallery.id = series_id
		weak_gallery.tags = dict_of_tags

		TagDB.add_tags(weak_gallery)


	@staticmethod
	def get_tag_gallery(tag):
		"Returns all galleries with the given tag"
		pass

	@classmethod
	def get_ns_tags(cls):
		"Returns a dict of all tags with namespace as key and list of tags as value"
		cursor = cls.execute(cls, 'SELECT namespace_id, tag_id FROM tags_mappings')
		ns_tags = {}
		ns_id_history = {} # to avoid unesseccary DB fetching
		for t in cursor.fetchall():
			try:
				# get namespace
				if not t['namespace_id'] in ns_id_history:
					c = cls.execute(cls, 'SELECT namespace FROM namespaces WHERE namespace_id=?', (t['namespace_id'],))
					ns = c.fetchone()['namespace']
					ns_id_history[t['namespace_id']] = ns
				else:
					ns = ns_id_history[t['namespace_id']]
				# get tag
				c = cls.execute(cls, 'SELECT tag FROM tags WHERE tag_id=?', (t['tag_id'],))
				tag = c.fetchone()['tag']
				# put in dict
				if ns in ns_tags:
					ns_tags[ns].append(tag)
				else:
					ns_tags[ns] = [tag]
			except:
				continue
		return ns_tags

	@staticmethod
	def get_tags_from_namespace(namespace):
		"Returns a dict with namespace as key and list of tags as value"
		pass

	@staticmethod
	def get_ns_tags_to_gallery(ns_tags):
		"""
		Returns all galleries linked to the namespace tags.
		Receives a dict like this: {"namespace":["tag1","tag2"]}
		"""
		pass

	@classmethod
	def get_all_tags(cls):
		"""
		Returns all tags in database in a list
		"""
		cursor = cls.execute(cls, 'SELECT tag FROM tags')
		tags = [t['tag'] for t in cursor.fetchall()]
		return tags

	@classmethod
	def get_all_ns(cls):
		"""
		Returns all namespaces in database in a list
		"""
		cursor = cls.execute(cls, 'SELECT namespace FROM namespaces')
		ns = [n['namespace'] for n in cursor.fetchall()]
		return ns


class HashDB(DBBase):
	"""
	Contains the following methods:

	get_gallery_hashes -> returns all hashes with the given gallery id in a list
	get_gallery_hash -> returns hash of chapter specified. If page is specified, returns hash of chapter page
	gen_gallery_hashes <- generates hashes for gallery's chapters and inserts them to db
	rebuild_gallery_hashes <- inserts hashes into DB only if it doesnt already exist
	"""

	@classmethod
	def get_gallery_hashes(cls, gallery_id):
		"Returns all hashes with the given gallery id in a list"
		cursor = cls.execute(cls, 'SELECT hash FROM hashes WHERE series_id=?',
				(gallery_id,))
		hashes = []
		try:
			for row in cursor.fetchall():
				hashes.append(row['hash'])
		except IndexError:
			return []
		return hashes

	@classmethod
	def get_gallery_hash(cls, gallery_id, chapter, page=None):
		"""
		returns hash of chapter. If page is specified, returns hash of chapter page
		"""
		assert isinstance(gallery_id, int)
		assert isinstance(chapter, int)
		if page:
			assert isinstance(page, int)
		chap_id = ChapterDB.get_chapter_id(gallery_id, chapter)
		if not chap_id:
			return None
		if page:
			exceuting = ["SELECT hash FROM hashes WHERE series_id=? AND chapter_id=? AND page=?",
					 (gallery_id, chap_id, page)]
		else:
			exceuting = ["SELECT hash FROM hashes WHERE series_id=? AND chapter_id=?",
					 (gallery_id, chap_id)]
		hashes = []
		c = cls.execute(cls, *exceuting)
		for h in c.fetchall():
			try:
				hashes.append(h['hash'])
			except KeyError:
				pass
		return hashes

	@classmethod
	def gen_gallery_hash(cls, gallery, chapter, page=None):
		"""
		Generate hash for a specific chapter.
		Set page to only generate specific page
		page: 'mid' or number
		Returns dict with chapter number or 'mid' as key and hash as value
		"""
		assert isinstance(gallery, Gallery)
		assert isinstance(chapter, int)
		if page:
			assert isinstance(page, (int, str))
		if gallery.id:
			chap_id = ChapterDB.get_chapter_id(gallery.id, chapter)
		chap = gallery.chapters[chapter]
		try:
			if gallery.is_archive:
				raise NotADirectoryError
			imgs = sorted([x.path for x in scandir.scandir(chap.path)])
			pages = {}
			for n, i in enumerate(imgs):
				pages[n] = i

			if page:
				pages = {}
				if page == 'mid':
					imgs = imgs[len(imgs)//2]
					pages[len(imgs)//2] = imgs
				else:
					imgs = imgs[page]
					pages = {page:imgs}

		except NotADirectoryError:
			temp_dir = os.path.join(gui_constants.temp_dir, str(uuid.uuid4()))
			is_archive = gallery.is_archive
			try:
				if is_archive:
					zip = ArchiveFile(gallery.path)
				else:
					zip = ArchiveFile(chap.path)
			except gui_constants.CreateArchiveFail:
				log_e('Could not generate hash: CreateZipFail')
				return {}
			pages = {}
			if page:
				p = 0
				if page == 'mid':
					if is_archive:
						con = zip.dir_contents(chap.path)
						p = len(con)//2
						img = con[p]
					else:
						img = zip.namelist()[len(zip.namelist())//2]
						p = len(zip.namelist())//2
				else:
					p = page
					if is_archive:
						con = zip.dir_contents(chap.path)
						img = con[p]
					else:
						img = zip.namelist()[p]
				pages = {p:zip.extract(img, temp_dir)}

			else:
				if is_archive:
					temp_dir = zip.extract(chap.path, temp_dir)
				else:
					zip.extract_all(temp_dir)
				imgs = sorted([x.path for x in scandir.scandir(temp_dir)])
				for n, i in enumerate(imgs):
					pages[n] = i

		def look_exists(hash):
			"""check if hash already exists in database
			returns hash, else returns None"""
			c = cls.execute(cls, 'SELECT hash FROM hashes WHERE hash = ?', (hash,))
			try: # exists
				return c.fetchone()['hash']
			except TypeError: # doesnt exist
				return None
			except IndexError:
				return None
		hashes = {}
		for i in pages:
			with open(pages[i], 'rb') as f:
				hashes[i] = generate_img_hash(f)
		if gallery.id:
			executing = []
			for h in hashes:
				if not look_exists(hashes[h]):
					executing.append((hashes[h], gallery.id, chap_id, h,))
			cls.executemany(cls, 'INSERT INTO hashes(hash, series_id, chapter_id, page) VALUES(?, ?, ?, ?)',
				   executing)
		if page == 'mid':
			return {'mid':list(hashes.values())[0]}
		else:
			return hashes

	@classmethod
	def gen_gallery_hashes(cls, gallery):
		"Generates hashes for gallery's first chapter and inserts them to DB"
		if gallery.id:
			chap_id = ChapterDB.get_chapter_id(gallery.id, 0)
		chap = gallery.chapters[0]
		try:
			if gallery.is_archive:
				raise NotADirectoryError
			imgs = scandir.scandir(chap.path)
			# filter
		except NotADirectoryError:
			# HACK: Do not need to extract all.. can read bytes from acrhive!!!
			t_p = os.path.join(gui_constants.temp_dir, str(uuid.uuid4()))
			try:
				if gallery.is_archive:
					zip = ArchiveFile(gallery.path)
					chap_path = zip.extract(chap.path, t_p)
				else:
					chap_path = t_p
					zip = ArchiveFile(chap.path)
					zip.extract_all(chap_path)
			except gui_constants.CreateArchiveFail:
				log_e('Could not generate hashes: CreateZipFail')
				return []
			imgs = scandir.scandir(chap_path)

		except FileNotFoundError:
			return False

		# filter
		imgs = [x.path for x in imgs if x.name.lower().endswith(tuple(IMG_FILES))]

		hashes = []
		for n, i in enumerate(sorted(imgs)):
			with open(i, 'rb') as img:
				hashes.append(generate_img_hash(img))

		if gallery.id and chap_id:
			executing = []
			for hash in hashes:
				executing.append((hash, gallery.id, chap_id, n,))

			cls.executemany(cls, 'INSERT INTO hashes(hash, series_id, chapter_id, page) VALUES(?, ?, ?, ?)',
				   executing)
		return hashes

	@staticmethod
	def rebuild_gallery_hashes(gallery):
		"Inserts hashes into DB only if it doesnt already exist"
		assert isinstance(gallery, Gallery)
		hashes = HashDB.get_gallery_hashes(gallery.id)

		if not hashes:
			hashes = HashDB.gen_gallery_hashes(gallery)
		return hashes

	@classmethod
	def del_gallery_hashes(cls, gallery_id):
		"Deletes all hashes linked to the given gallery id"
		cls.execute(cls, 'DELETE FROM hashes WHERE series_id=?', (gallery_id,))


class Gallery:
	"""
	Base class for a gallery.
	Available data:
	id -> Not to be editied. Do not touch.
	title <- [list of titles] or str
	profile <- path to thumbnail
	path <- path to gallery
	artist <- str
	chapters <- {<number>:<path>}
	chapter_size <- int of number of chapters
	info <- str
	fav <- int (1 for true 0 for false)
	type <- str (Manga? Doujin? Other?)
	language <- str
	status <- "unknown", "completed" or "ongoing"
	tags <- list of str
	pub_date <- date
	date_added <- date, will be defaulted to today if not specified
	last_read <- timestamp (e.g. time.time())
	last_update <- last updated file
	last_read <- an integer telling us how many times the gallery has been opened
	hashes <- a list of hashes of the gallery's chapters
	exed <- indicator on if gallery metadata has been fetched
	valid <- a bool indicating the validity of the gallery

	Takes ownership of ChaptersContainer
	"""
	def __init__(self):

		self.id = None # Will be defaulted.
		self.title = None
		self.profile = None
		self.path = None
		self.path_in_archive = ""
		self.is_archive = 0
		self.artist = None
		self._chapters = ChaptersContainer(self)
		self.info = None
		self.fav = 0
		self.type = None
		self.link = ""
		self.language = ""
		self.status = None
		self.tags = {}
		self.pub_date = None
		self.date_added = datetime.datetime.now().replace(microsecond=0)
		self.last_read = None
		self.last_update = None
		self.times_read = 0
		self.valid = False
		self._db_v = None
		self.hashes = []
		self.exed = 0
		self._cache_id = 0 # used by custom delegate to cache profile
		self.state = 0

	@property
	def chapters(self):
		return self._chapters

	@chapters.setter
	def chapters(self, chp_cont):
		assert isinstance(chp_cont, ChaptersContainer)
		chp_cont.set_parent(self)
		self._chapters = chp_cont

	def gen_hashes(self):
		"Generate hashes while inserting them into DB"
		if not self.hashes:
			hash = HashDB.gen_gallery_hashes(self)
			if hash:
				self.hashes = hash
				return True
			else:
				return False
		else:
			return True

	def validate(self):
		"Validates gallery, returns status"
		# TODO: Extend this
		validity = []
		status = False

		#if not self.hashes:
		#	HashDB.gen_gallery_hashes(self)
		#	self.hashes = HashDB.get_gallery_hashes(self.id)

		if all(validity):
			status = True
			self.valid = True
		return status

	def invalidities(self):
		"""
		Checks all attributes for invalidities.
		Returns list of string with invalid attribute names
		"""
		return []

	def __contains__(self, key):
		if isinstance(key, Chapter):
			return self.chapters.__contains__(key)
		elif isinstance(key, str):
			is_exclude = False if key[0] == '-' else True
			key = key[1:] if not is_exclude else key
			default = False if is_exclude else True
			if key:
				# check in title/artist/language
				found = False
				if not ':' in key:
					for g_attr in [self.title, self.artist, self.language]:
						if not g_attr:
							continue
						if gui_constants.ALLOW_SEARCH_REGEX:
							if utils.regex_search(key, g_attr):
								found = True
								break
						else:
							if utils.search_term(key, g_attr):
								found = True
								break

				# check in tag
				if not found:
					key = key.lower()
					tags = key.split(':')
					ns = tag = ''
					if len(tags) > 1:
						ns = tags[0].capitalize()
						tag = tags[1].lower()
					else:
						tag = tags[0].lower()

					if ns:
						key_word = ['none', 'null']
						if ns == 'Tag' and tag in key_word:
							if not self.tags:
								return is_exclude
						elif ns == 'Artist' and tag in key_word:
							if not self.artist:
								return is_exclude
						elif ns == 'Status' and tag in key_word:
							if not self.status or self.status == 'Unknown':
								return is_exclude
						elif ns == 'Language' and tag in key_word:
							if not self.language:
								return is_exclude
						elif ns == 'Url' and tag in key_word:
							if not self.link:
								return is_exclude
						elif ns in ('Descr', 'Description') and tag in key_word:
							if not self.info or self.info == 'No description..':
								return is_exclude
						elif ns == 'Type' and tag in key_word:
							if not self.type:
								return is_exclude
						elif ns in ('Publication', 'Pub_date', 'Pub date') and tag in key_word:
							if not self.pub_date:
								return is_exclude 

					if gui_constants.ALLOW_SEARCH_REGEX:
						if ns:
							for x in self.tags:
								if utils.regex_search(ns, x):
									for t in self.tags[x]:
										if utils.regex_search(tag, t):
											return is_exclude
					else:
						if ns:
							if ns in self.tags:
								if tag in self.tags[ns]:
									return is_exclude
						else:
							for x in self.tags:
								if tag in self.tags[x]:
									return is_exclude
				else:
					return is_exclude
		return default

	def __str__(self):
		string = """
		ID: {}
		Title: {}
		Profile Path: {}
		Path: {}
		Path In Archive: {}
		Is Archive: {}
		Author: {}
		Description: {}
		Favorite: {}
		Type: {}
		Language: {}
		Status: {}
		Tags: {}
		Publication Date: {}
		Date Added: {}
		Exed: {}
		Hashes: {}

		Chapters: {}
		""".format(self.id, self.title, self.profile, self.path.encode(errors='ignore'), self.path_in_archive.encode(errors='ignore'),
			 self.is_archive, self.artist, self.info, self.fav, self.type, self.language, self.status, self.tags,
			 self.pub_date, self.date_added, self.exed, len(self.hashes), self.chapters)
		return string

class Chapter:
	"""
	Base class for a chapter
	Contains following attributes:
	parent -> The ChapterContainer it belongs in
	gallery -> The Gallery it belongs to
	path -> path to chapter
	number -> chapter number
	pages -> chapter pages
	in_archive -> 1 if the chapter path is in an archive else 0
	"""
	def __init__(self, parent, gallery, number=0, path="", pages=0, in_archive=0):
		self.parent = parent
		self.gallery = gallery
		self.path = path
		self.number = number
		self.pages = pages
		self.in_archive = in_archive

	def __lt__(self, other):
		return self.number < other.number

	def __str__(self):
		s = """
		Chapter: {}
		Path: {}
		Pages: {}
		in_archive: {}
		""".format(self.number, self.path, self.pages, self.in_archive)
		return s

	@property
	def next_chapter(self):
		try:
			return self.parent[self.number+1]
		except KeyError:
			return None

	@property
	def previous_chapter(self):
		try:
			return self.parent[self.number-1]
		except KeyError:
			return None

	# TODO: implement this
	def open(self):
		pass

class ChaptersContainer:
	"""
	A container for chapters.
	Acts like a list/dict of chapters.

	Iterable returns a ordered list of chapters
	Sets to gallery.chapters
	"""
	def __init__(self, gallery=None):
		self.parent = None
		self._data = {}

		if gallery:
			gallery.chapters = self

	def set_parent(self, gallery):
		assert isinstance(gallery, (Gallery, None))
		self.parent = gallery
		for n in self._data:
			chap = self._data[n]
			chap.gallery = gallery

	def add_chapter(self, chp, overwrite=True, db=False):
		"Add a chapter of Chapter class to this container"
		assert isinstance(chp, Chapter), "Chapter must be an instantiated Chapter class"
		
		if not overwrite:
			try:
				_ = self._data[chp.number]
				raise gui_constants.ChapterExists
			except KeyError:
				pass
		chp.gallery = self.parent
		chp.parent = self
		self[chp.number] = chp
		

		if db:
			# TODO: implement this
			pass

	def create_chapter(self, number=None):
		"""
		Creates Chapter class with the next chapter number or passed number arg and adds to container
		The chapter will be returned
		"""
		if number:
			chp = Chapter(self, self.parent, number=number)
		else:
			next_number = 0
			for n in list(self._data.keys()):
				if n > next_number:
					next_number = n
			chp = Chapter(self, self.parent, number=next_number)
			self[next_number] = chp
		return chp

	def get_chapter(self, number):
		return self[number]

	def get_all_chapters(self):
		return list(self._data.values())

	def count(self):
		return len(self)

	def pop(self, key, default=None):
		return self._data.pop(key, default)

	def __len__(self):
		return len(self._data)

	def __getitem__(self, key):
		return self._data[key]

	def __setitem__(self, key, value):
		assert isinstance(key, int), "Key must be a chapter number"
		assert isinstance(value, Chapter), "Value must be an instantiated Chapter class"
		
		if value.gallery != self.parent:
			raise gui_constants.ChapterWrongParentGallery
		self._data[key] = value

	def __delitem__(self, key):
		del self._data[key]

	def __iter__(self):
		return iter([self[c] for c in sorted(self._data.keys())])

	def __bool__(self):
		return bool(self._data)

	def __str__(self):
		s = ""
		for c in self:
			s += '\n' + '{}'.format(c)
		if not s:
			return '{}'
		return s

	def __contains__(self, key):
		if key.gallery == self.parent and key in [self.data[c] for c in self._data]:
			return True
		return False


class AdminDB(QObject):
	DONE = pyqtSignal(bool)
	PROGRESS = pyqtSignal(int)
	DATA_COUNT = pyqtSignal(int)
	def __init__(self, parent=None):
		super().__init__(parent)

	def rebuild_galleries(self):
		galleries = add_method_queue(GalleryDB.get_all_gallery, False)
		if galleries:
			self.DATA_COUNT.emit(len(galleries))
			log_i('Rebuilding galleries')
			for n, g in enumerate(galleries, 1):
				add_method_queue(GalleryDB.rebuild_gallery, False, g)
				self.PROGRESS.emit(n)
		self.DONE.emit(True)

	def rebuild_thumbs(self):
		# add_method_queue(GalleryDB.clear_thumb_dir, True)
		# TODO okay, so I added this method above in order to completely clear
		# the thumbnail cache, because I noticed that sometimes
		# the database and thumbnail cache might be inconsistent, I could not
		# reproduce the case in which this happened, even though it did
		# so I just implemented it just in case, maybe you could add
		# a new confirmation dialog for the user to select if he would
		# like to do a complete wipe of the cache
		# I might do this later, depending on how you prefer, I'm not very
		# experienced with Qt, though. So, yeah, you could just wipe this
		# and things would be fine, probably.

		galleries = add_method_queue(GalleryDB.get_all_gallery, False)
		if galleries:
			self.DATA_COUNT.emit(len(galleries))
			log_i('Rebuilding galleries')
			for n, g in enumerate(galleries, 1):
				add_method_queue(GalleryDB.rebuild_thumb, False, g)
				self.PROGRESS.emit(n)
		self.DONE.emit(True)

class DatabaseEmitter(QObject):
	"""
	Fetches and emits database records
	START: emitted when fetching from DB occurs
	DONE: emitted when the initial fetching from DB finishes
	"""
	GALLERY_EMITTER = pyqtSignal(list)
	START = pyqtSignal()
	DONE = pyqtSignal()
	COUNT_CHANGE = pyqtSignal()
	_DB = DBBase()

	RUN = False

	def __init__(self):
		super().__init__()
		self._current_data = gui_constants.GALLERY_DATA
		self._fetch_count = 200
		self._offset = 0
		self._fetching = False
		self.count = 0
		self._finished = False
		self.update_count()

	def update_count(self):
		if not self._fetching:
			self._fetching = True
			oldc = self.count
			self.count = GalleryDB.gallery_count()
			if oldc != self.count:
				self.COUNT_CHANGE.emit()
			self._fetching = False

	def can_fetch_more(self):
		if len(self._current_data) < self.count:
			return True
		else:
			if not self._finished:
				self._finished = True
				self.DONE.emit()
			return False

	def fetch_more(self):
		if not self.RUN:
			return
		self.START.emit()
		def get_records():
			self._fetching = True
			remaining = self.count - len(self._current_data)
			rec_to_fetch = min(remaining, self._fetch_count)
			c = add_method_queue(self._DB.execute, False, 'SELECT * FROM series LIMIT {}, {}'.format(
				self._offset, rec_to_fetch))
			self._offset += rec_to_fetch
			new_data = c.fetchall()
			gallery_list = add_method_queue(GalleryDB.gen_galleries, False, new_data)
			#self._current_data.extend(gallery_list)
			if gallery_list:
				self.GALLERY_EMITTER.emit(gallery_list)
			self._fetching = False
		if not self._fetching:
			# TODO: redo this? 
			thread = threading.Thread(target=get_records, name='DatabaseEmitter')
			thread.start()


if __name__ == '__main__':
	#unit testing here
	pass
