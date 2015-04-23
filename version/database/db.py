from . import db_constants, index

class Self_:
	"""
	Provides methods to edit the DB
	"""
	pass

class DatabaseItem:
	"""A base class for all database items.
	This might make it easier to extend database items (e.g special kinds of series')
	"""
	pass


# maybe move this to chapter module?

#class ChapterDB:
#	"""
#	Provides the following database methods:
#		add_chapter -> adds chapter into db
#		chapter_size -> returns amount of manga (can be used for indexing)
#		del_chapter -> (don't think this will be used, but w/e) NotImplementedError
#	"""

#	@staticmethod
#	def add_chapters(metadata):
#		#NOTE: add index when adding
#		#OBS: STILL NEED TO FIGURE OUT A WAY FOR
#		# MANGA AND CHAPTERS TO BE LINKED
#		"Adds chapters linked to manga into database"
#		pass

#	@staticmethod
#	def chapter_size(manga_id):
#		"""Returns the amount of chapters for the given
#		manga id
#		"""
#		pass

#	@staticmethod
#	def del_chapter():
#		"Raises NotImplementedError"
#		raise NotImplementedError


if __name__ == '__main__':
	raise RuntimeError("Unit tests not yet implemented")
	# unit tests here!