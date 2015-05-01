from .. import utils
from . import db, metadata # REMEMBER TO IMPLEMENT SERIALIZING METHOD IN DB

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
	def get_manga_by_artist(artist):
		"Returns manga with given artist"
		pass

	@staticmethod
	def get_manga_by_title(title):
		"Returns manga with given title"
		pass

	@staticmethod
	def get_manga_by_metadata(metdata):
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

class ChapterDB:
	"""
	Provides the following database methods:
		add_chapter -> adds chapter into db
		chapter_size -> returns amount of manga (can be used for indexing)
		del_chapter -> (don't think this will be used, but w/e) NotImplementedError
	"""

	@staticmethod
	def add_chapters(metadata):
		#NOTE: add index when adding
		#OBS: STILL NEED TO FIGURE OUT A WAY FOR
		# MANGA AND CHAPTERS TO BE LINKED
		"Adds chapters linked to manga into database"
		pass

	@staticmethod
	def get_chapters(id):
		"Returns chapters matching the recieved ID(s), takes a str or list"
		pass

	@staticmethod
	def chapter_size(manga_id):
		"""Returns the amount of chapters for the given
		manga id
		"""
		pass

	@staticmethod
	def del_chapter():
		"Raises NotImplementedError"
		raise NotImplementedError

##TODO: IMPLEMENT add_manga and add_chapter in db

##TODO: IMPLEMENT INDEXING
class Series(db.DatabaseItem):
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
	def __init__(self):
		super().__init__()

		self.data = {}
		#      "title":"Unknown", "artist":"Anonymous", "Summary":"No Info", "type":"Unknown", "genres":[], "tags":[],
		#	  "pub_date":"", "date_added":utils.today(), "last_read":utils.today()}
		self.chapters = {}
		
		self.title = ""
		self.title_image = ""
		#self._artist = artist
		#self._info = info
		#self._type = type_
		#self._genres = genres
		#self._tags = tags
		#self._pub_date = pub_date
		#self._date_added = date_added
		#self._last_read = last_read


		
		#MangaDB.add_manga(self) # add manga with no chapters into db

		#NOTE: this way we can implement drag & drop, so when zip/cbz/folder of manga
		# is dropped it handles the chapters itself
		#self._do_chapters(self._chapters) # handle received chapters and add them to db
	


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

		#	metadataChapterDB.add_chapter(md)

		for chap in chap_object:
			for pages in chap_object[chap]:
				pass
				#raise NotImplementedError("Adding chapters not yet implemented")
				#_do_chapter(numb, pages)



if __name__ == '__main__':
	#unit testing here
	date = today()
	print(date)
	#raise RuntimeError("Unit testing still not implemented")
