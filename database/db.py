import db_constants
import index

class Self_:
	"""
	Provides methods to edit the DB
	"""
	pass

class DatabaseItem:
	"A base class for MangaDB and ChapterDB"
	pass

class MangaDB(DatabaseItem):
	"""
	Provides the following s methods:
		add_manga -> adds manga into db
		set_manga_title -> changes manga title
		manga_size -> returns amount of manga (can be used for indexing)
		del_manga -> deletes the manga with the given id recursively
	"""
	db_path = db_constants.DB_PATH

	def __init__(self):
		return super().__init__(self.__class__)

	@staticmethod
	def add_manga(title, metadata):
		#NOTE: add index when adding
		"Adds manga into database"
		#NOTE: received metadata looks like this:
		#{"genres":self._genres, "publishing date":self._pub_date,
		#"date added":self._date_added, "last read":self._last_read}
		pass

	@staticmethod
	def manga_size():
		"""Returns the amount of mangas in db.
		Can also be used for indexing (i.e the returned value + 1)
		"""
		pass

	@staticmethod
	def del_manga(manga_id):
		"Deletes manga with the given id recursively."
		pass

class ChapterDB(DatabaseItem):
	"""
	Provides the following database methods:
		add_chapter -> adds chapter into db
		chapter_size -> returns amount of manga (can be used for indexing)
		del_chapter -> (don't think this will be used, but w/e) NotImplementedError
	"""

	@staticmethod
	def add_chapters(metadata):
		#NOTE: add index when adding
		"Adds chapters linked to manga into database"
		#NOTE: received metadata looks like this:
		#{"link":self.title, "chapter":chapter_number,
		#"pages":pages, "metadata":self._chap_metadata}
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


if __name__ == '__main__':
	raise RuntimeError("Unit tests not yet implemented")
	# unit tests here!