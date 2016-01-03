#"""
#This file is part of Happypanda.
#Happypanda is free software: you can redistribute it and/or modify
#it under the terms of the GNU General Public License as published by
#the Free Software Foundation, either version 2 of the License, or
#any later version.
#Happypanda is distributed in the hope that it will be useful,
#but WITHOUT ANY WARRANTY; without even the implied warranty of
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#GNU General Public License for more details.
#You should have received a copy of the GNU General Public License
#along with Happypanda.  If not, see <http://www.gnu.org/licenses/>.
#"""

import os, sqlite3, threading, queue
import logging, time, shutil

from . import db_constants
log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical

def hashes_sql(cols=False):
	sql = """
		CREATE TABLE IF NOT EXISTS hashes(
					hash_id INTEGER PRIMARY KEY,
					hash BLOB,
					series_id INTEGER,
					chapter_id INTEGER,
					page INTEGER,
					FOREIGN KEY(series_id) REFERENCES series(series_id),
					FOREIGN KEY(chapter_id) REFERENCES chapters(chapter_id)
					UNIQUE(hash, series_id, chapter_id, page));
	"""

	col_list = [
	'hash_id INTEGER PRIMARY KEY',
	'hash BLOB',
	'series_id INTEGER',
	'chapter_id INTEGER',
	'page INTEGER'
	]
	if cols:
		return sql, col_list
	return sql

def series_sql(cols=False):
	sql = """
		CREATE TABLE IF NOT EXISTS series(
					series_id INTEGER PRIMARY KEY,
					title TEXT,
					artist TEXT,
					profile BLOB,
					series_path BLOB,
					is_archive INTEGER,
					path_in_archive BLOB,
					info TEXT,
					fav INTEGER,
					type TEXT,
					link BLOB,
					language TEXT,
					status TEXT,
					pub_date TEXT,
					date_added TEXT,
					last_read TEXT,
					times_read INTEGER,
					exed INTEGER NOT NULL DEFAULT 0,
					db_v REAL);
		"""
	col_list = [
		'series_id INTEGER PRIMARY KEY',
		'title TEXT',
		'artist TEXT',
		'profile BLOB',
		'series_path BLOB',
		'is_archive INTEGER',
		'path_in_archive BLOB',
		'info TEXT',
		'fav INTEGER',
		'type TEXT',
		'link BLOB',
		'language TEXT',
		'status TEXT',
		'pub_date TEXT',
		'date_added TEXT',
		'last_read TEXT',
		'times_read INTEGER',
		'exed INTEGER NOT NULL DEFAULT 0',
		'db_v REAL',
		]
	if cols:
		return sql, col_list
	return sql

def chapters_sql(cols=False):
	sql = """
		CREATE TABLE IF NOT EXISTS chapters(
					chapter_id INTEGER PRIMARY KEY,
					series_id INTEGER,
					chapter_title TEXT NOT NULL DEFAULT '',
					chapter_number INTEGER,
					chapter_path BLOB,
					pages INTEGER,
					in_archive INTEGER,
					FOREIGN KEY(series_id) REFERENCES series(series_id));
		"""
	col_list = [
		'chapter_id INTEGER PRIMARY KEY',
		'series_id INTEGER',
		"chapter_title TEXT NOT NULL DEFAULT ''",
		'chapter_number INTEGER',
		'chapter_path BLOB',
		'pages INTEGER',
		'in_archive INTEGER',
		]
	if cols:
		return sql, col_list
	return sql

def namespaces_sql(cols=False):
	sql = """
		CREATE TABLE IF NOT EXISTS namespaces(
					namespace_id INTEGER PRIMARY KEY,
					namespace TEXT NOT NULL UNIQUE);
		"""
	col_list = [
		'namespace_id INTEGER PRIMARY KEY',
		'namespace TEXT NOT NULL UNIQUE'
		]
	if cols:
		return sql, col_list
	return sql

def tags_sql(cols=False):
	sql = """
		CREATE TABLE IF NOT EXISTS tags(
					tag_id INTEGER PRIMARY KEY,
					tag TEXT NOT NULL UNIQUE);
		"""
	col_list = [
		'tag_id INTEGER PRIMARY KEY',
		'tag TEXT NOT NULL UNIQUE'
		]
	if cols:
		return sql, col_list
	return sql

def tags_mappings_sql(cols=False):
	sql ="""
		CREATE TABLE IF NOT EXISTS tags_mappings(
					tags_mappings_id INTEGER PRIMARY KEY,
					namespace_id INTEGER,
					tag_id INTEGER,
					FOREIGN KEY(namespace_id) REFERENCES namespaces(namespace_id),
					FOREIGN KEY(tag_id) REFERENCES tags(tag_id)
					UNIQUE(namespace_id, tag_id));
		"""
	col_list = [
		'tags_mappings_id INTEGER PRIMARY KEY',
		'namespace_id INTEGER',
		'tag_id INTEGER'
		]
	if cols:
		return sql, col_list
	return sql

def series_tags_mappings_sql(cols=False):
	sql ="""
		CREATE TABLE IF NOT EXISTS series_tags_map(
					series_id INTEGER,
					tags_mappings_id INTEGER,
					FOREIGN KEY(series_id) REFERENCES series(series_id),
					FOREIGN KEY(tags_mappings_id) REFERENCES tags_mappings(tags_mappings_id)
					UNIQUE(series_id, tags_mappings_id));
		"""
	col_list = [
		'series_id INTEGER',
		'tags_mappings_id INTEGER'
		]
	if cols:
		return sql, col_list
	return sql

def list_sql(cols=False):
	sql ="""
		CREATE TABLE IF NOT EXISTS list(
					list_id INTEGER PRIMARY KEY,
					list_name TEXT NOT NULL DEFAULT '');
		"""
	col_list = [
		'list_id INTEGER PRIMARY KEY',
		"list_name TEXT NOT NULL DEFAULT ''",
		]
	if cols:
		return sql, col_list
	return sql

def series_list_map_sql(cols=False):
	sql ="""
		CREATE TABLE IF NOT EXISTS series_list_map(
					list_id INTEGER NOT NULL,
					series_id INTEGER INTEGER NOT NULL,
					FOREIGN KEY(list_id) REFERENCES list(list_id),
					FOREIGN KEY(series_id) REFERENCES series(series_id)
					UNIQUE(list_id, series_id));
		"""
	col_list = [
		'list_id INTEGER NOT NULL',
		'series_id INTEGER INTEGER NOT NULL',
		]
	if cols:
		return sql, col_list
	return sql

STRUCTURE_SCRIPT = series_sql()+chapters_sql()+namespaces_sql()+tags_sql()+tags_mappings_sql()+\
	series_tags_mappings_sql()+hashes_sql()+list_sql()+series_list_map_sql()

def global_db_convert(conn):
	"""
	Takes care of converting tables and columns.
	Don't use this method directly. Use the add_db_revisions instead.
	"""
	log_i('Converting tables')
	c = conn.cursor()
	series, series_cols = series_sql(True)
	chapters, chapters_cols = chapters_sql(True)
	namespaces, namespaces_cols = namespaces_sql(True)
	tags, tags_cols = tags_sql(True)
	tags_mappings, tags_mappings_cols = tags_mappings_sql(True)
	series_tags_mappings, series_tags_mappings_cols = series_tags_mappings_sql(True)
	hashes, hashes_cols = hashes_sql(True)
	_list, list_cols = list_sql(True)
	series_list_map, series_list_map_cols = series_list_map_sql(True)
	
	t_d = {}
	t_d['series'] = series_cols
	t_d['chapters'] = chapters_cols
	t_d['namespaces'] = namespaces_cols
	t_d['tags'] = tags_cols
	t_d['tags_mappings'] = tags_mappings_cols
	t_d['series_tags_mappings'] = series_tags_mappings_cols
	t_d['hashes'] = hashes_cols
	t_d['list'] = list_cols
	t_d['series_list_map'] = series_list_map_cols

	log_d('Checking table structures')
	c.executescript(STRUCTURE_SCRIPT)
	conn.commit()

	log_d('Checking columns')
	for table in t_d:
		for col in t_d[table]:
			try:
				c.execute('ALTER TABLE {} ADD COLUMN {}'.format(table, col))
				log_d('Added new column: {}'.format(col))
			except:
				log_d('Skipped column: {}'.format(col))
	conn.commit()
	log_d('Commited DB changes')
	return c

def add_db_revisions(old_db):
	"""
	Adds specific DB revisions items.
	Note: pass a path to db
	"""
	log_i('Converting DB')
	conn = sqlite3.connect(old_db, check_same_thread=False)
	conn.row_factory = sqlite3.Row

	log_i('Converting tables and columns')
	c = global_db_convert(conn)

	log_d('Updating DB version')
	c.execute('UPDATE version SET version=? WHERE 1', (db_constants.CURRENT_DB_VERSION,))
	conn.commit()
	conn.close()
	return

def create_db_path(db_path=db_constants.DB_PATH):
	head = os.path.split(db_path)[0]
	os.makedirs(head, exist_ok=True)
	if not os.path.isfile(db_path):
		with open(db_path, 'x') as f:
			pass
	return db_path


def check_db_version(conn):
	"Checks if DB version is allowed. Raises dialog if not"
	vs = "SELECT version FROM version"
	c = conn.cursor()
	c.execute(vs)
	log_d('Checking DB Version')
	db_vs = c.fetchone()
	db_constants.REAL_DB_VERSION = db_vs[0]
	if db_vs[0] not in db_constants.DB_VERSION:
		msg = "Incompatible database"
		log_c(msg)
		log_d('Local database version: {}\nProgram database version:{}'.format(db_vs[0],
																		 db_constants.CURRENT_DB_VERSION))
		#ErrorQueue.put(msg)
		return False
	return True
	

def init_db(path=''):
	"""Initialises the DB. Returns a sqlite3 connection,
	which will be passed to the db thread.
	"""

	def db_layout(cursor):
		c = cursor
		# version
		c.execute("""
		CREATE TABLE IF NOT EXISTS version(version REAL)
		""")

		c.execute("""INSERT INTO version(version) VALUES(?)""", (db_constants.CURRENT_DB_VERSION,))

		c.executescript(STRUCTURE_SCRIPT)

	def new_db(p, new=False):
		conn = sqlite3.connect(p, check_same_thread=False)
		conn.row_factory = sqlite3.Row
		if new:
			c = conn.cursor()
			db_layout(c)
			conn.commit()
		return conn

	if path:
		if os.path.isfile(path):
			conn = new_db(path)
		else:
			create_db_path(path)
			conn = new_db(path, True)
		return conn

	if os.path.isfile(db_constants.DB_PATH):
		conn = new_db(db_constants.DB_PATH)
		if not check_db_version(conn):
			return None
	else:
		create_db_path()
		conn = new_db(db_constants.DB_PATH, True)

	conn.execute("PRAGMA foreign_keys = on")
	return conn

class DBBase:
	"The base DB class. _DB_CONN should be set at runtime on startup"
	_DB_CONN = None
	_LOCK = False
	_AUTO_COMMIT = True

	def __init__(self, **kwargs):
		pass

	@classmethod
	def begin(cls):
		"Useful when modifying for a large amount of data"
		cls._AUTO_COMMIT = False
		cls.execute(cls, "BEGIN TRANSACTION")
		print("STARTED DB OPTIMIZE")

	@classmethod
	def end(cls):
		"Called to commit and end transaction"
		cls._AUTO_COMMIT = True
		cls._DB_CONN.commit()
		print("ENDED DB OPTIMIZE")

	def execute(self, *args):
		"Same as cursor.execute"
		if not self._DB_CONN:
			raise db_constants.NoDatabaseConnection
		log_d('DB Query: {}'.format(args).encode(errors='ignore'))
		if self._AUTO_COMMIT:
			try:
				try:
					with self._DB_CONN:
						return self._DB_CONN.execute(*args)
				except sqlite3.InterfaceError:
						return self._DB_CONN.execute(*args)
			except sqlite3.IntegrityError:
				print(args)

		else:
			return self._DB_CONN.execute(*args)
	
	def executemany(self, *args):
		"Same as cursor.executemany"
		if not self._DB_CONN:
			raise db_constants.NoDatabaseConnection
		log_d('DB Query: {}'.format(args).encode(errors='ignore'))
		try:
			if self._AUTO_COMMIT:
				with self._DB_CONN:
					return self._DB_CONN.executemany(*args)
			else:
				return self._DB_CONN.executemany(*args)
		except sqlite3.IntegrityError:
			print(args)
			raise ValueError
		self._LOCK = False

	def commit(self):
		self._DB_CONN.commit()

if __name__ == '__main__':
	raise RuntimeError("Unit tests not yet implemented")
	# unit tests here!