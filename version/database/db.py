import sqlite3

import os

from . import index, db_constants


class Database:
	"""Provides methods to access the DB
	"""
	def __init__(self):
		if os.path.isfile(db_constants.DB_PATH):
			self.conn = sqlite3.connect(db_constants.DB_PATH)
			# TODO: check the version of the database
		else:
			self.conn = sqlite3.connect(db_constants.DB_PATH)
			c = self.conn.cursor()
			# version
			c.execute("""
			CREATE TABLE IF NOT EXISTS version(version INTEGER)
			""")

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

			# chapters
			c.execute("""
			CREATE TABLE IF NOT EXISTS chapters(chapter_id INTERGER UNIQUE, chapter_number INTEGER,
									chapter_path TEXT, FOREIGN KEY(series_id) REFERENCES series(series_id))
			""")

			# tags & namespaces
			# nvm namespaces for now
			#c.execute("""
			#CREATE TABLE namespaces(namespace_id INTERGER PRIMARY KEY, namespace TEXT)
			#""")
			c.execute("""
			CREATE TABLE IF NOT EXISTS tags(tag_id INTERGER PRIMARY KEY, tag TEXT)
			""")

			## tags_mapping
			#c.execute("""
			#CREATE TABLE tags_mappings(tags_mappings_id INTEGER PRIMARY KEY, namespace_id INTERGER,
			#							tag_id INTEGER, hash_id INTEGER)
			#""")
			
			# series tags
			c.execute("""
			CREATE TABLE IF NOT EXISTS series_tags(FOREIGN KEY(series_id) REFERENCES series(series_id),
										FOREIGN KEY(tag_id) REFERENCES tags(tag_id))
			""")


	def exec(self, list_of_cmds):
		"Receives a list containing string of SQL commands to execute"
		assert isinstance(list_of_cmds, list), "DB only receives lists containting sql cmds!"
		c = self.conn.cursor()
		for string in list_of_cmds:
			c.execute(string)
		self.conn.commit()

if __name__ == '__main__':
	raise RuntimeError("Unit tests not yet implemented")
	# unit tests here!