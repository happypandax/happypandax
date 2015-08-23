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
import logging

from PyQt5.QtSql import QSqlDatabase

from . import db_constants
log = logging.getLogger(__name__)
log_i = log.info
log_d = log.debug
log_w = log.warning
log_e = log.error
log_c = log.critical

def init_db():
	db = QSqlDatabase.addDatabase('QSQLITE')
	db.setDatabaseName(db_constants.DB_PATH)
	log_i('Open database: {}'.format(db.open()))
	db_constants.DATABASE = db

def hashes_sql(cols=False):
	sql = """
		CREATE TABLE IF NOT EXISTS hashes(
					hash_id INTEGER PRIMARY KEY,
					hash BLOB,
					series_id INTEGER,
					chapter_id INTEGER,
					page INTEGER,
					FOREIGN KEY(series_id) REFERENCES series(series_id),
					FOREIGN KEY(chapter_id) REFERENCES chapters(chapter_id))
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
					last_update TEXT,
					times_read INTEGER,
					exed INTEGER NOT NULL DEFAULT 0,
					db_v REAL)
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
		'last_update TEXT',
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
					chapter_number INTEGER,
					chapter_path BLOB,
					in_archive INTEGER,
					FOREIGN KEY(series_id) REFERENCES series(series_id))
		"""
	col_list = [
		'chapter_id INTEGER PRIMARY KEY',
		'series_id INTEGER',
		'chapter_number INTEGER',
		'chapter_path BLOB',
		'in_archive INTEGER',
		]
	if cols:
		return sql, col_list
	return sql

def namespaces_sql(cols=False):
	sql = """
		CREATE TABLE IF NOT EXISTS namespaces(
					namespace_id INTEGER PRIMARY KEY,
					namespace TEXT NOT NULL UNIQUE)
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
					tag TEXT NOT NULL UNIQUE)
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
					FOREIGN KEY(tag_id) REFERENCES tags(tag_id))
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
					FOREIGN KEY(tags_mappings_id) REFERENCES tags_mappings(tags_mappings_id))
		"""
	col_list = [
		'series_id INTEGER',
		'tags_mappings_id INTEGER'
		]
	if cols:
		return sql, col_list
	return sql

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
	
	t_d = {}
	t_d['series'] = series_cols
	t_d['chapters'] = chapters_cols
	t_d['namespaces'] = namespaces_cols
	t_d['tags'] = tags_cols
	t_d['tags_mappings'] = tags_mappings_cols
	t_d['series_tags_mappings'] = series_tags_mappings_cols
	t_d['hashes'] = hashes_cols

	log_d('Checking table structures')
	c.execute(series_sql())
	c.execute(chapters_sql())
	c.execute(namespaces_sql())
	c.execute(tags_sql())
	c.execute(tags_mappings_sql())
	c.execute(series_tags_mappings_sql())
	c.execute(hashes_sql())
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

	c.execute('SELECT version FROM version')
	version = c.fetchone()[0]
	if not version:
		version = 0
	log_i('Start DB version: {}'.format(version))
	vs = 0

	if 0.18 > version:
		vs = 0.18

	log_d('Updating DB version')
	c.execute('UPDATE version SET version=? WHERE 1', (db_constants.CURRENT_DB_VERSION,))
	conn.commit()
	log_i('End DB version: {}'.format(vs))
	c.close()
	conn.close()
	log_d('Closing DB connection'.format(vs))
	ResultQueue.put('done')
	return

def create_db_path(db_name=None):
	t_path = os.path.split(db_constants.DB_PATH)
	if db_name:
		db_path = os.path.join(t_path[0], db_name)
		t_path = (t_path[0], db_name)
	else:
		db_path = db_constants.DB_PATH

	for p in t_path[:-1]:
		if not os.path.isdir(p):
			os.mkdir(p)
	else:
		if not os.path.isfile(db_path):
			with open(db_path, 'x') as f:
				pass


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
	

def init_db(test=False):
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

		# series
		c.execute(series_sql())

		#chapters
		c.execute(chapters_sql())

		# tags & namespaces
		c.execute(namespaces_sql())

		c.execute(tags_sql())

		# tags_mapping
		c.execute(tags_mappings_sql())
						
		# series tags
		c.execute(series_tags_mappings_sql())
		
		# hashes
		c.execute(hashes_sql())

	if test:
		db_test_path = os.path.join(os.path.split(db_constants.DB_PATH)[0],'database_test.db')
		if os.path.isfile(db_test_path):
			conn = sqlite3.connect(db_test_path, check_same_thread=False)
			conn.row_factory = sqlite3.Row
		else:
			create_db_path('database_test.db')
			conn = sqlite3.connect(db_test_path, check_same_thread=False)
			conn.row_factory = sqlite3.Row
			c = conn.cursor()
			db_layout(c)
			conn.commit()
		return conn

	if os.path.isfile(db_constants.DB_PATH):
		conn = sqlite3.connect(db_constants.DB_PATH, check_same_thread=False)
		conn.row_factory = sqlite3.Row
		if not check_db_version(conn):
			return None
	else:
		create_db_path()
		conn = sqlite3.connect(db_constants.DB_PATH, check_same_thread=False)
		conn.row_factory = sqlite3.Row
		c = conn.cursor()
		db_layout(c)
		conn.commit()
	return conn

CommandQueue = queue.Queue() #Receives a 2D list of cmds, and puts them in the queue
ResultQueue = queue.Queue() #Receives a cursor object and puts it in the result queue
ErrorQueue = queue.Queue()

# TODO: Maybe look at the priority method? 

class DBThread:
	'''A class containing methods to interact with a database in a thread-safe manner.
	A connection must be passed when instantiating. This class works with queues.
	IMPORTANT: This method puts a cursor in the ResultQueue.
	This means that to avoid order and wrong returns, you must
	get the cursor out of the queue
	'''
	def __init__(self, db_conn):
		assert isinstance(db_conn, sqlite3.Connection), "A sqlite3 connection must be passed"
		self.conn = db_conn
		#self.vs_checked = False #to prevent multiple version cheking this instance
		
		query_thread = threading.Thread(target=self.query, args=(CommandQueue, ResultQueue,), daemon=True)
		query_thread.start()
		log_d('Start Database Thread: OK')

	def query(self, cmd_queue, result_queue):
		"""Important: This method puts a cursor in the ResultQueue.
		This means that to avoid order and wrong returns, you must
		get the cursor out of the queue"""
		assert isinstance(cmd_queue, queue.Queue), "You must pass a queue from the queue system module"
		assert isinstance(result_queue, queue.Queue), "You must pass a queue from the queue system module"

		check_db_version(self.conn)
		while True:
			list_of_cmds = cmd_queue.get()
			# TODO: implement error handling. Idea: make it put status code in resultqueue or spawn a dialog?
			c = self.conn.cursor()
			for cmd in list_of_cmds:
				try:
					log_d("{}".format(cmd[0]).encode(errors='ignore'))
					log_d("{}".format(cmd[1]).encode(errors='ignore'))
					c.execute(cmd[0], cmd[1])
				except IndexError:
					log_d("{}".format(cmd[0]).encode(errors='ignore'))
					c.execute(cmd[0])
				except sqlite3.OperationalError:
					log.exception('An error occured while trying to access DB')
				except:
					log.exception('An unknown error occured while trying to access DB')

			self.conn.commit()
			result_queue.put(c)
			cmd_queue.task_done()

if __name__ == '__main__':
	raise RuntimeError("Unit tests not yet implemented")
	# unit tests here!