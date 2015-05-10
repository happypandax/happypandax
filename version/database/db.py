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
			self.conn.row_factory = sqlite3.Row
		else:
			self._create_db_path()
			self.conn = sqlite3.connect(db_constants.DB_PATH)
			self.conn.row_factory = sqlite3.Row
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
			CREATE TABLE IF NOT EXISTS series(
						series_id INTEGER PRIMARY KEY,
						title TEXT,
						artist TEXT,
						profile BLOB,
						series_path BLOB,
						info TEXT,
						type TEXT,
						pub_date TEXT,
						date_added TEXT,
						last_read TEXT,
						last_update TEXT)
			""")

			#chapters
			c.execute("""
			CREATE TABLE IF NOT EXISTS chapters(
						chapter_id INTEGER PRIMARY KEY,
						series_id INTEGER,
						chapter_number INTEGER,
						chapter_path BLOB,
						FOREIGN KEY(series_id) REFERENCES series(series_id))
			""")

			# tags & namespaces
			# nvm namespaces for now
			#c.execute("""
			#CREATE TABLE namespaces(namespace_id INTERGER PRIMARY KEY, namespace TEXT)
			#""")
			c.execute("""
			CREATE TABLE IF NOT EXISTS tags(
						tag_id INTEGER PRIMARY KEY,
						tag TEXT NOT NULL)
			""")

			## tags_mapping
			#c.execute("""
			#CREATE TABLE tags_mappings(tags_mappings_id INTEGER PRIMARY KEY, namespace_id INTERGER,
			#							tag_id INTEGER, hash_id INTEGER)
			#""")
						
			# series tags
			c.execute("""
			CREATE TABLE IF NOT EXISTS series_tags(
						series_id INTEGER,
						tag_id INTEGER,
						FOREIGN KEY(series_id) REFERENCES series(series_id),
						FOREIGN KEY(tag_id) REFERENCES tags(tag_id))""")

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
		vs = [["SELECT version FROM version"]]
		db_vs = self.exec(vs).fetchone()
		if db_vs[0] not in db_constants.DB_VERSION:
			msg = "The database is not compatible with the current version of the program"
			exception_handler(msg)
			raise Exception(msg)

	def exec(self, list_of_cmds):
		'''Receives a 2D list containing strings of SQL commands to execute.
		NB: Pass only one statment if you expect a return.
		'''
		assert isinstance(list_of_cmds, list), "DB only receives lists containting sql cmds!"
		# TODO: implement error handling. Idea: make it return an exception (possible?)
		c = self.conn.cursor()
		for cmd in list_of_cmds:
			try:
				c.execute(cmd[0], cmd[1])
			except IndexError:
				c.execute(cmd[0])
		self.conn.commit()
		return c

	def reset(self):
		"WARNING: Resets the DB! You'll lose all data."
		os.remove(db_constants.DB_PATH)
		self.__init__()

DB = Database()

if __name__ == '__main__':
	raise RuntimeError("Unit tests not yet implemented")
	# unit tests here!