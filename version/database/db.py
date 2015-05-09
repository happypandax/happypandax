import os, sqlite3

from . import db_constants
from ..utils import exception_handler


class Database:
	"""Provides methods to access the DB
	"""
	def __init__(self):
		# TODO: add a more tourough search in the DB
		if os.path.isfile(db_constants.DB_PATH):
			self.conn = sqlite3.connect(db_constants.DB_PATH)
		else:
			self._create_db_path()
			self.conn = sqlite3.connect(db_constants.DB_PATH)
			c = self.conn.cursor()
			# version
			c.execute("""
			CREATE TABLE IF NOT EXISTS version(version REAL)
			""")

			c.execute("""INSERT INTO version(version) VALUES(?)""", (db_constants.CURRENT_DB_VERSION,))

			# hash
			# nvm the complicated stuff for now
			#c.execute("""
			#CREATE TABLE hashes(hash_id INTERGER PRIMARY KEY, hash BLOB)
			#""")

			# Series
			c.execute("""
			CREATE TABLE IF NOT EXISTS series(series_id INTEGER PRIMARY KEY, title TEXT, artist TEXT,
								profile TEXT, series_path TEXT, info TEXT, type TEXT,
								pub_date TEXT, date_added TEXT, last_read TEXT)
			""")

			#chapters
			c.execute("""
			CREATE TABLE chapters(chapter_id INTERGER UNIQUE, series_id INTEGER, chapter_number INTEGER,
									chapter_path TEXT, FOREIGN KEY(series_id) REFERENCES series(series_id))
			""")

			# tags & namespaces
			# nvm namespaces for now
			#c.execute("""
			#CREATE TABLE namespaces(namespace_id INTERGER PRIMARY KEY, namespace TEXT)
			#""")
			c.execute("""
			CREATE TABLE IF NOT EXISTS tags(tag_id INTERGER PRIMARY KEY, tag TEXT NOT NULL)
			""")

			## tags_mapping
			#c.execute("""
			#CREATE TABLE tags_mappings(tags_mappings_id INTEGER PRIMARY KEY, namespace_id INTERGER,
			#							tag_id INTEGER, hash_id INTEGER)
			#""")
						
			# series tags
			c.execute("""
			CREATE TABLE IF NOT EXISTS series_tags(series_id INTEGER, tag_id INTEGER,
										FOREIGN KEY(series_id) REFERENCES series(series_id),
										FOREIGN KEY(tag_id) REFERENCES tags(tag_id))
			""")

			self.conn.commit()
		self._check_db_version()
	
	def _create_db_path(self):
		t_path = os.path.split(db_constants.DB_PATH)
		for p in t_path[:-1]:
			if not os.path.isdir(p):
				os.mkdir(p)
		else:
			if not os.path.isfile(db_constants.DB_PATH):
				with open(db_constants.DB_PATH, 'w') as f:
					f.write('')

	def _check_db_version(self):
		"Checks if DB version is allowed. Raises dialog if not"
		vs = ["SELECT version FROM version"]
		db_vs = self.exec(vs).fetchone()
		if db_vs[0] not in db_constants.DB_VERSION:
			msg = "The database is not compatible with the current version of the program"
			exception_handler(msg)
			raise Exception(msg)

	def exec(self, list_of_cmds):
		'''Receives a list containing string of SQL commands to execute.
		NB: haven't tested yet, but you should pass a list with 1 string if
		you expect a return.
		'''
		assert isinstance(list_of_cmds, list), "DB only receives lists containting sql cmds!"
		c = self.conn.cursor()
		for string in list_of_cmds:
			c.execute(string)
		self.conn.commit()
		return c

if __name__ == '__main__':
	raise RuntimeError("Unit tests not yet implemented")
	# unit tests here!