from euler import today
from database import db # REMEMBER TO IMPLEMENT SERIALIZING METHOD IN DB
##TODO: IMPLEMENT add_manga and add_chapter in db

class Manga:
	""" Creates a manga with the following metadata:
	Title -> str
	Chapters -> [[<chapter_number>, [<pages>]]]
				e.g [[1, [pg1, pg2]], [2, [pg1, pg2]]]
	Genres -> list
	Publishing date -> (not sure yet... prolly string: dd/mm/yy)
	Date Added -> date, will be defaulted on init
	Last Read -> timestamp (e.g. time.time()), will be defaulted to date on init
	"""
	def __init__(self, title, chapters, genres=[], pub_date="",
			  date_added=today(), last_read=today()):
		self._title = title
		self._chapters = chapters
		self._genres = genres
		self._pub_date = pub_date
		self._date_added = date_added
		self._last_read = last_read
		self._metadata = []

		self._do_metadata() # make initial metadata
		
		db.add_manga(self.title, self._metadata) # add manga with no chapters into db

		#NOTE: this way we can implement drag & drop, so when zip/cbz/folder of manga
		# is dropped it handles the chapters itself
		self._do_chapters(self._chapters) # handle received chapters and add them to db

	def set_title(self, new_title):
		"Changes manga title"
		pass
	
	def set_genres(self, new_genres):
		"""Changes genres
		Note: think about existing genres and how to deal with them
		"""
		pass

	@property
	def title(self):
		"Returns title in str"
		return self._title

	@property
	def chapter(self, chapter_number):
		"Returns a specific chapter path"
		pass

	@property
	def chapters(self):
		"""Returns a dict with all chapters
		-> chapter_number:path
		"""
		pass

	@property
	def last_read(self):
		"Returns last read timestamp"
		pass

	@property
	def date_added(self):
		"Returns date added str e.g. dd Mmm YYYY"
		d = "{} {} {}".format(self._date_added[0], self._date_added[1], self._date_added[2])
		return d

	def _do_chapters(self, chap_object):
		"""Only meant to be used internally and once, but
		can be used outside too. Just remember, that
		chapters will be overwritten
		"""
		
		def _do_chapter(chapter_number, pages):
			"sends metadata to db"
			_chap_metadata = [] #meta data for the individual chapter
			metadata = {"title":self.title, "chapter":chapter_number, "pages":pages, "metadata":self._chap_metadata}

			db.add_chapter(metadata)

		for chap in chap_object:
			for numb, pages in chap:
				_do_chapter(numb, pages)

	def _do_metadata(self):
		"will create initial metadata for the manga"

		self._metadata = {"genres":self._genres, "publishing date":self._pub_date,
					"date added":self._date_added, "last read":self._last_read}

class MangaContainer(Manga):
	"""Meant to be used by DB when retriveing manga
	Title -> str
	Chapters -> [[<chapter_number>, [<pages>]]]
				e.g [[1, [pg1, pg2]], [2, [pg1, pg2]]]
	Metadata -> dict
	"""
	def __init__(self, title, chapters, metadata):
		pass