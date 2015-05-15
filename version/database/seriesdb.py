import datetime, os, threading, queue, uuid # for unique filename
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage

from ..utils import today
from .db import CommandQueue, ResultQueue
from ..gui import gui_constants
from .db_constants import THUMBNAIL_PATH, IMG_FILES

def gen_thumbnail(chapter_path, width=gui_constants.THUMB_W_SIZE-2,
				height=gui_constants.THUMB_H_SIZE): # 2 to align it properly.. need to redo this
	"""Generates a thumbnail with unique filename in the cache dir.
	Returns absolute path to the created thumbnail
	"""
	assert isinstance(chapter_path, str), "Path to chapter should be a string"

	img_path_queue = queue.Queue()
	# generate a cache dir if required
	if not os.path.isdir(THUMBNAIL_PATH):
		os.mkdir(THUMBNAIL_PATH)

	def generate(cache, chap_path, w, h, img_queue):
		img_path = os.path.join(chap_path, [x for x in sorted(os.listdir(chap_path)) if x[-3:] in IMG_FILES][0]) #first image in chapter
		suff = img_path[-4:] # the image ext with dot
		
		# generate unique file name
		file_name = str(uuid.uuid4()) + suff
		new_img_path = os.path.join(cache, (file_name))
		
		# Do the scaling
		image = QImage()
		image.load(img_path)
		image = image.scaled(w, h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
		image.save(new_img_path, quality=100)

		abs_path = os.path.abspath(new_img_path)
		img_queue.put(abs_path)
		return True

	thread = threading.Thread(target=generate, args=(THUMBNAIL_PATH,
												  chapter_path, width, height,
												  img_path_queue,))
	thread.start()
	thread.join()
	return img_path_queue.get()

def series_map(row, series):
	series.title = row['title']
	series.artist = row['artist']
	series.profile = bytes.decode(row['profile'])
	series.path = bytes.decode(row['series_path'])
	series.info = row['info']
	series.language = row['language']
	series.status = row['status']
	series.type = row['type']
	series.fav = row['fav']
	series.pub_date = row['pub_date']
	series.last_update = row['last_update']
	series.last_read = row['last_read']
	series.date_added = row['date_added']
	return series

def default_exec(object):
	def check(obj):
		if obj == None:
			return "None"
		else:
			return obj
	executing = [["""INSERT INTO series(title, artist, profile, series_path, 
					info, type, fav, status, pub_date, date_added, last_read, last_update)
				VALUES(:title, :artist, :profile, :series_path, :info, :type, :fav,
					:status, :pub_date, :date_added, :last_read, :last_update)""",
				{
				'title':check(object.title),
				'artist':check(object.artist),
				'profile':str.encode(object.profile),
				'series_path':str.encode(object.path),
				'info':check(object.info),
				'fav':check(object.fav),
				'type':check(object.type),
				'language':check(object.language),
				'status':check(object.status),
				'pub_date':check(object.pub_date),
				'date_added':check(object.date_added),
				'last_read':check(object.last_read),
				'last_update':check(object.last_update)
				}
				]]
	return executing

class SeriesDB:
	"""
	Provides the following s methods:
		get_all_series -> returns a list of all series (<Series> class) currently in DB
		get_series_by_id -> Returns series with given id
		get_series_by_artist -> Returns series with given artist
		get_series_by_title -> Returns series with given title
		get_series_by_tags -> Returns series with given list of tags
		add_series -> adds series into db
		add_series_return -> adds series into db AND returns the added series
		set_series_title -> changes series title
		series_count -> returns amount of series (can be used for indexing)
		del_series -> deletes the series with the given id recursively
	"""
	def __init__(self):
		raise Exception("SeriesDB should not be instantiated")

	@staticmethod
	def modify_series(series_id, title=False, artist=False, info=False, type=False, fav=False,
				   language=False, status=False, pub_date=False):
		"Modifies series with given series id"
		pass

	@staticmethod
	def fav_series_set(series_id, fav):
		"Set fav on series with given series id, and returns the series"
		executing = [["UPDATE series SET fav=? WHERE series_id=?", (fav, series_id)]]
		CommandQueue.put(executing)
		c = ResultQueue.get()
		del c
		ex = [["SELECT * FROM series WHERE series_id=?", (series_id,)]]
		CommandQueue.put(ex)
		cursor = ResultQueue.get()
		row = cursor.fetchone()
		series = Series()
		series.id = row['series_id']
		series = series_map(row, series)
		return series
		

	@staticmethod
	def get_all_series():
		"""Careful, might crash with very large libraries i think...
		Returns a list of all series (<Series> class) currently in DB"""
		executing = [["SELECT * FROM series"]]
		CommandQueue.put(executing)
		cursor = ResultQueue.get()
		all_series = cursor.fetchall()
		series_list = []
		for series_row in all_series:
			series = Series()
			series.id = series_row['series_id']
			series = series_map(series_row, series)
			series_list.append(series)

		return series_list

	@staticmethod
	def get_series_by_id(id):
		"Returns series with given id"
		assert isinstance(id, int), "Provided ID is invalid"
		executing = [["SELECT * FROM series WHERE series_id=?", (id,)]]
		CommandQueue.put(executing)
		cursor = ResultQueue.get()
		row = cursor.fetchone()
		series = Series()
		series.id = row['series_id']
		series = series_map(row, series)
		return series


	@staticmethod
	def get_series_by_artist(artist):
		"Returns series with given artist"
		assert isinstance(artist, str), "Provided artist is invalid"
		executing = [["SELECT * FROM series WHERE artist=?", (artist,)]]
		CommandQueue.put(executing)
		cursor = ResultQueue.get()
		row = cursor.fetchone() # TODO: an artist can have multiple series' :^)
		series = Series()
		series.id = row['series_id']
		series = series_map(row, series)
		return series

	@staticmethod
	def get_series_by_title(title):
		"Returns series with given title"
		assert isinstance(id, int), "Provided title is invalid"
		executing = [["SELECT * FROM series WHERE title=?", (title,)]]
		CommandQueue.put(executing)
		cursor = ResultQueue.get()
		row = cursor.fetchone()
		series = Series()
		series.id = row['series_id']
		series = series_map(row, series)
		return series

	@staticmethod
	def get_series_by_tags(list_of_tags):
		"Returns series with given list of tags"
		assert isinstance(list_of_tags, list), "Provided tag(s) is/are invalid"
		pass

	@staticmethod
	def get_series_by_fav(list_of_tags):
		"Returns a list of series with fav set to true (1)"
		assert isinstance(list_of_tags, list), "Provided tag(s) is/are invalid"
		x = 1
		executing = [["SELECT * FROM series WHERE fav=?", (x,)]]
		CommandQueue.put(executing)
		cursor = ResultQueue.get()
		
		series_list = []
		for row in cursor.fetchall():
			series = Series()
			series.id = row["series_id"]
			series = series_map(row, series)
			series_list.append(series)
		return series_list

	@staticmethod
	def add_series(object):
		"Receives an object of class Series, and appends it to DB"
		"Adds series of <Series> class into database"
		assert isinstance(object, Series), "add_series method only accept Series items"

		object.profile = gen_thumbnail(object.chapters[0])

		executing = default_exec(object)
		CommandQueue.put(executing)
		cursor = ResultQueue.get()
		series_id = cursor.lastrowid
		object.id = series_id
		ChapterDB.add_chapters(object)

	@staticmethod
	def add_series_return(object):
		"Receives an object of class Series, and appends it to DB"
		"Adds series of <Series> class into database AND returns the added series"
		assert isinstance(object, Series), "add_series method only accept Series items"

		object.profile = gen_thumbnail(object.chapters[0])

		executing = default_exec(object)
		CommandQueue.put(executing)
		cursor = ResultQueue.get()
		series_id = cursor.lastrowid
		object.id = series_id
		ChapterDB.add_chapters(object)

		executing2 = [["SELECT * FROM series WHERE series_id=?", (series_id,)]]
		CommandQueue.put(executing2)
		cursor = ResultQueue.get()
		row = cursor.fetchone()
		series = Series()
		series.id = row['series_id']
		series = series_map(row, series)
		return series
		# TODO: Add a way to insert tags

	@staticmethod
	def series_count():
		"""Returns the amount of series' in db.
		"""
		pass

	@staticmethod
	def del_series(manga_id):
		"Deletes series with the given id recursively."
		pass


class ChapterDB:
	"""
	Provides the following database methods:
		add_chapter -> adds chapter into db
		add_chapter_raw -> links chapter to the given seires id, and adds into db
		get_chapters_for_series-> returns a dict with chapters linked to the given series_id
		get_chapter-> returns a dict with chapter matching the given chapter_id
		chapter_size -> returns amount of manga (can be used for indexing)
		del_chapter -> (don't think this will be used, but w/e) NotImplementedError
	"""

	@staticmethod
	def add_chapters(series_object):
		"Adds chapters linked to series into database"
		assert isinstance(series_object, Series), "Parent series need to be of class Series"
		series_id = series_object.id
		for chap_number in series_object.chapters:
			chap_path = str.encode(series_object.chapters[chap_number])
			executing = [["""
			INSERT INTO chapters(series_id, chapter_number, chapter_path)
			VALUES(:series_id, :chapter_number, :chapter_path)""",
			{'series_id':series_id,
			'chapter_number':chap_number,
			'chapter_path':chap_path}
			]]
			CommandQueue.put(executing)
			# neccessary to keep order... feels awkward, will prolly redo this.
			d = ResultQueue.get()
			del d

	def add_chapters_raw(series_id):
		"Adds chapter(s) to a series with the received series_id"
		pass

	@staticmethod
	def get_chapters_for_series(series_id):
		"""Returns a dict of chapters matching the received series_id
		{<chap_number>:<chap_path>}
		"""
		assert isinstance(series_id, int), "Please provide a valid series ID"
		executing = [["""SELECT chapter_number, chapter_path
							FROM chapters WHERE series_id=?""",
							(series_id,)]]
		CommandQueue.put(executing)
		cursor = ResultQueue.get()
		rows = cursor.fetchall()
		chapters = {}
		for row in rows:
			chapters[row['chapter_number']] = bytes.decode(row['chapter_path'])

		return chapters


	@staticmethod
	def get_chapter(id):
		"""Returns a dict of chapter matching the recieved chapter_id
		{<chap_number>:<chap_path>}
		"""
		assert isinstance(id, int), "Please provide a valid chapter ID"
		executing = [["""SELECT chapter_number, chapter_path
							FROM chapters WHERE chapter_id=?""",
							(id,)]]
		CommandQueue.put(executing)
		cursor = ResultQueue.get()
		rows = cursor.fetchall()
		chapters = {}
		for row in rows:
			chapters[row['chapter_number']] = bytes.decode(row['chapter_path'])

		return chapters

	@staticmethod
	def chapter_size(series_id):
		"""Returns the amount of chapters for the given
		manga id
		"""
		pass

	@staticmethod
	def del_chapter():
		"Raises NotImplementedError"
		raise NotImplementedError

class Series:
	"""Base class for a series.
	Available data:
	title <- [list of titles] or str
	profile <- path to thumbnail
	path <- path to series
	artist <- str
	chapters <- {<number>:<path>}
	chapter_size <- int of number of chapters
	info <- str
	type <- str (Manga? Doujin? Other?)
	status <- "unknown", "completed" or "ongoing"
	tags <- list of str
	pub_date <- string: dd/mm/yy
	date_added <- date, will be defaulted to today if not specified
	last_read <- timestamp (e.g. time.time())
	last_update <- last updated file
	"""
	def __init__(self):
		
		self.id = None # Will be defaulted.
		self.title = None
		self.profile = None
		self.path = None
		self.artist = None
		self.chapters = {}
		self.info = None
		self.fav = 0
		self.type = None
		self.language = None
		self.status = None
		self.tags = None
		self.pub_date = None
		self.date_added = datetime.date.today()
		self.last_read = None
		self.last_update = None



if __name__ == '__main__':
	#unit testing here
	date = today()
	print(date)
	#raise RuntimeError("Unit testing still not implemented")
