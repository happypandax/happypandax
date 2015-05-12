import datetime, os
from ..utils import today
from .db import CommandQueue, StaleQueue, ResultQueue

class SeriesDB:
	"""
	Provides the following s methods:
		get_all_series -> returns a list of all series (<Series> class) currently in DB
		get_series_by_id -> Returns series with given id
		get_series_by_artist -> Returns series with given artist
		get_series_by_title -> Returns series with given title
		get_series_by_tags -> Returns series with given list of tags
		add_series -> adds series into db
		set_series_title -> changes series title
		series_count -> returns amount of series (can be used for indexing)
		del_series -> deletes the series with the given id recursively
	"""
	def __init__(self):
		raise Exception("SeriesDB should not be instantiated")

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
			series.title = series_row['title']
			series.artist = series_row['artist']
			series.profile = bytes.decode(series_row['profile'])
			series.path = bytes.decode(series_row['series_path'])
			series.info = series_row['info']
			series.type = series_row['type']
			series.pub_date = series_row['pub_date']
			series.date_added = series_row['date_added']
			series.last_read = series_row['last_read']
			series.last_update = series_row['last_update']

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
		series.title = row['title']
		series.artist = row['artist']
		series.profile = bytes.decode(row['profile'])
		series.path = bytes.decode(row['series_path'])
		series.info = row['info']
		series.type = row['type']
		series.pub_date = row['pub_date']
		series.date_added = row['date_added']
		series.last_read = row['last_read']
		series.last_update = row['last_update']
		return series


	@staticmethod
	def get_series_by_artist(artist):
		"Returns series with given artist"
		assert isinstance(artist, str), "Provided artist is invalid"
		executing = [["SELECT * FROM series WHERE artist=?", (artist,)]]
		CommandQueue.put(executing)
		cursor = ResultQueue.get()
		row = cursor.fetchone()
		series = Series()
		series.id = row['series_id']
		series.title = row['title']
		series.artist = row['artist']
		series.profile = bytes.decode(row['profile'])
		series.path = bytes.decode(row['series_path'])
		series.info = row['info']
		series.type = row['type']
		series.pub_date = row['pub_date']
		series.date_added = row['date_added']
		series.last_read = row['last_read']
		series.last_update = row['last_update']
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
		series.title = row['title']
		series.artist = row['artist']
		series.profile = bytes.decode(row['profile'])
		series.path = bytes.decode(row['series_path'])
		series.info = row['info']
		series.type = row['type']
		series.pub_date = row['pub_date']
		series.date_added = row['date_added']
		series.last_read = row['last_read']
		series.last_update = row['last_update']
		return series

	@staticmethod
	def get_series_by_tags(list_of_tags):
		"Returns series with given list of tags"
		assert isinstance(list_of_tags, list), "Provided tag(s) is/are invalid"
		pass

	@staticmethod
	def add_series(object):
		"Receives an object of class Series, and appends it to DB"
		"Adds series of <Series> class into database"
		assert isinstance(object, Series), "add_series method only accept Series items"

		executing = [["""INSERT INTO series(title, artist, profile, series_path, 
						info,type, pub_date, date_added, last_read, last_update)
					VALUES(:title, :artist, :profile, :series_path, :info, :type,
						:pub_date, :date_added, :last_read, :last_update)""",
					{
					'title':object.title,
					'artist':object.artist,
					'profile':str.encode(object.profile),
					'series_path':str.encode(object.path),
					'info':object.info,
					'type':object.type,
					'pub_date':object.pub_date,
					'date_added':object.date_added,
					'last_read':object.last_read,
					'last_update':object.last_update
					}
					]]
		CommandQueue.put(executing)
		cursor = ResultQueue.get()
		series_id = cursor.lastrowid
		object.id = series_id
		ChapterDB.add_chapters(object)
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
			StaleQueue.put(executing)

	def add_chapters_raw(series_id):
		"Adds chapter(s) to a series with the received series_id"
		pass

	@staticmethod
	def get_chapters_for_series(series_id):
		"""Returns a dict of chapters matching the received series_id
		{<chap_number>:<chap_path>}
		"""
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
	def get_chapters(id):
		"""Returns a dict of chapters matching the recieved chapter_id
		{<chap_number>:<chap_path>}
		"""
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
	status <- "completed" or "ongoing"
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
		self.type = None
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
