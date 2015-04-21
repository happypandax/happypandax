from euler import today
from database import db, metadata # REMEMBER TO IMPLEMENT SERIALIZING METHOD IN DB
##TODO: IMPLEMENT add_manga and add_chapter in db

##TODO: IMPLEMENT INDEXING
class Manga:
	""" Creates a manga with the following parameters:
	title -> str
	chapters -> [[<chapter_number>, [<pages>]]]
				e.g [[1, [pg1, pg2]], [2, [pg1, pg2]]]
	genres -> list
	pub_date -> (not sure yet... prolly string: dd/mm/yy)
	date_added -> date, will be defaulted on init
	last_read -> timestamp (e.g. time.time()), will be defaulted to date on init
	"""
	def __init__(self, title, chapters, genres=[], pub_date="",
			  date_added=today(), last_read=today()):
		# index will most likely be returned from database class
		self._index = "" # STILL NEED TO IMPLEMENT
		self._title = title
		self._chapters = chapters
		self._genres = genres
		self._pub_date = pub_date
		self._date_added = date_added
		self._last_read = last_read
		self._metadata = []

		self._do_metadata() # make initial metadata
		
		db.MangaDB.add_manga(self.title, self._metadata) # add manga with no chapters into db

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
			#OBS: still need to implement indexing
			md = {"link":self._index, "chapter":chapter_number,
			   "pages":pages, "metadata":self._chap_metadata}

			metadata.ChapterDB.add_chapter(md)

		for chap in chap_object:
			for numb, pages in chap:
				_do_chapter(numb, pages)

	def _do_metadata(self):
		"will create initial metadata for the manga"

		self._metadata = {"genres":self._genres, "publishing date":self._pub_date,
					"date added":self._date_added, "last read":self._last_read}

class MangaContainer(Manga):
	"""Meant to be used by DB when retriveing manga
	id -> int
	title -> str
	chapters -> [[<chapter_number>, [<pages>]]]
				e.g [[1, [pg1, pg2]], [2, [pg1, pg2]]]
	metadata -> dict
	"""
	def __init__(self, id, title, chapters, metadata):
		pass


if __name__ == '__main__':
	#unit testing here
	pass
