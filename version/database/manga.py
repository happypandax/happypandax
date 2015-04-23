from .. import constants
from . import db, metadata # REMEMBER TO IMPLEMENT SERIALIZING METHOD IN DB

##TODO: IMPLEMENT add_manga and add_chapter in db

##TODO: IMPLEMENT INDEXING
class MangaContainer(db.DatabaseItem):
	""" Creates a manga.
	Params:
			title <- [list of titles]
			artist <- str
			chapters <- {<chapter_number>:{1:page1, 2:page2, 3:page3}}
	The following params wil be packed into a metadata dict:
	info <- str
	type <- str
	genres <- list
	pub_date <- (not sure yet... prolly string: dd/mm/yy)
	date_added <- date, will be defaulted on init
	last_read <- timestamp (e.g. time.time()), will be defaulted to date on init
	"""
	def __init__(self, title, artist, chapters, info = "No Info", type_="Unknown", genres=[], tags=[],
			  pub_date="", date_added=constants.today(), last_read=constants.today()):
		super().__init__()
		self._title = title
		self._artist = artist
		self._chapters = chapters
		self._info = info
		self._type = type_
		self._genres = genres
		self._tags = tags
		self._pub_date = pub_date
		self._date_added = date_added
		self._last_read = last_read
		self._metadata = ""

		self._do_metadata() # make  initial metadata
		
		db.MangaDB.add_manga(self) # add manga with no chapters into db

		#NOTE: this way we can implement drag & drop, so when zip/cbz/folder of manga
		# is dropped it handles the chapters itself
		self._do_chapters(self._chapters) # handle received chapters and add them to db

	def _do_chapters(self, chap_object):
		"""Only meant to be used internally and once, but
		can be used outside too. Just remember, that
		chapters will be overwritten
		"""
		
		#DROPPED
		#def _do_chapter(chapter_number, pages):
		#	"sends metadata to db"
		#	_chap_metadata = [] #meta data for the individual chapter
		#	#OBS: still need to implement indexing
		#	md = {"link":self._index, "chapter":chapter_number,
		#	   "pages":pages, "metadata":self._chap_metadata}

		#	metadata.ChapterDB.add_chapter(md)

		for chap in chap_object:
			for pages in chap_object[chap]:
				pass
				#raise NotImplementedError("Adding chapters not yet implemented")
				#_do_chapter(numb, pages)

	def _do_metadata(self):
		"will create initial metadata for the manga"

		self._metadata = {"info":self._info, "type":self._type,
					"genres":self._genres, "tags":self._tags,
					"publishing date":self._pub_date,
					"date added":self._date_added, "last read":self._last_read}


class Manga(db.DatabaseItem):
	"""Meant to be used by DB and GridBox. Provides manga data.
	id <- int
	title <- str
	artist <- str
	chapters <- {<chapter_number>:{1:page1, 2:page2, 3:page3}}
	metadata <- dict
	Provides the following methods:
		set_genres -> changes genres
		---to be continued---
	"""
	def __init__(self, id, title, artist, info, chapters, metadata):
		super().__init__()
		self.id = id
		self.title = title
		self.artist = artist
		self.chapters = {"id":id, "chapters":chapters}
		self.metadata = metadata

	def set_title(self, new_title):
		"Changes manga title"
		pass
	
	def set_genres(self, new_genres):
		"""Changes genres
		Note: think about existing genres and how to deal with them
		"""
		pass

	def set_tags(self, new_tags):
		"""Changes tags
		Note: think about existing tags and how to deal with them
		"""
		pass

	@property
	def get_title(self):
		"Returns title in str"
		return self._title

	@property
	def get_chapter(self, chapter_number):
		"Returns a specific chapter path"
		pass

	@property
	def get_chapters(self):
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

class MangaDB:
	"""
	Provides the following s methods:
		get_all_manga -> returns a list of all manga (<Manga> class) currently in DB
		get_manga_by_id -> Returns manga with given id
		get_manga_by_artist -> Returns manga with given artist
		get_manga_by_title -> Returns manga with given title
		get_manga_by_metadata -> Returns manga with given metadata
		add_manga -> adds manga into db
		set_manga_title -> changes manga title
		manga_count -> returns amount of manga (can be used for indexing)
		del_manga -> deletes the manga with the given id recursively
	"""

	def __init__(self):
		pass

	@staticmethod
	def get_all_manga():
		"""Careful, might crash with large libraries
		returns a list of all manga (<Manga> class) currently in DB"""
		pass

	@staticmethod
	def get_manga_by_id(id):
		"Returns manga with given id"
		pass

	@staticmethod
	def get_manga_by_artist():
		"Returns manga with given artist"
		pass

	@staticmethod
	def get_manga_by_title():
		"Returns manga with given title"
		pass

	@staticmethod
	def get_manga_by_metadata():
		"Returns manga with given metadata"
		pass

	@staticmethod
	def add_manga(object):
		#NOTE: add index when adding
		"Adds manga into database"
		#NOTE: received metadata looks like this:
		#self._metadata = {"info":self._info, "type":self._type,
		#			"genres":self._genres, "tags":self._tags,
		#			"publishing date":self._pub_date,
		#			"date added":self._date_added, "last read":self._last_read}
		assert isinstance(object, DatabaseItem), "add_manga method only accept DatabaseItems"

	@staticmethod
	def manga_count():
		"""Returns the amount of mangas in db.
		Can also be used for indexing (i.e the returned value + 1)
		"""
		pass

	@staticmethod
	def del_manga(manga_id):
		"Deletes manga with the given id recursively."
		pass


if __name__ == '__main__':
	#unit testing here
	date = today()
	print(date)
	#raise RuntimeError("Unit testing still not implemented")
