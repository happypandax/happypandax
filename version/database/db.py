import os, sqlite3, threading, queue

from . import db_constants
from ..utils import exception_handler

def init_db():
	"""Initialises the DB. Returns a sqlite3 connection,
	which will be passed to the db thread.
	"""
	def create_db_path():
		t_path = os.path.split(db_constants.DB_PATH)
		for p in t_path[:-1]:
			if not os.path.isdir(p):
				os.mkdir(p)
		else:
			if not os.path.isfile(db_constants.DB_PATH):
				with open(db_constants.DB_PATH, 'w') as f:
					f.write('')

	if os.path.isfile(db_constants.DB_PATH):
		conn = sqlite3.connect(db_constants.DB_PATH, check_same_thread=False)
		conn.row_factory = sqlite3.Row
	else:
		create_db_path()
		conn = sqlite3.connect(db_constants.DB_PATH, check_same_thread=False)
		conn.row_factory = sqlite3.Row
		c = conn.cursor()
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

		conn.commit()
	return conn

CommandQueue = queue.Queue() #Receives a 2D list of cmds, and puts them in the queue
StaleQueue = queue.Queue() #Receives a 2D list of cmds, and puts them in the queue
ResultQueue = queue.Queue() #Receives a cursor object and puts it in the result queue

class DBThread:
	'''A class containing methods to interact with a database in a thread-safe manner.
	A connection must be passed when instantiating. This class works with queues.
	'''
	def __init__(self, db_conn):
		assert isinstance(db_conn, sqlite3.Connection), "A sqlite3 connection must be passed"
		self.conn = db_conn
		self.vs_checked = False #to prevent multiple version cheking this instance
		
		query_thread = threading.Thread(target=self.query, args=(CommandQueue, ResultQueue,))
		stale_query_thread = threading.Thread(target=self.stale_query, args=(StaleQueue,))
		query_thread.start()
		stale_query_thread.start()

	def query(self, cmd_queue, result_queue):
		"This method should be used when you expect a return"
		assert isinstance(cmd_queue, queue.Queue), "You must pass a queue from the queue system module"
		assert isinstance(result_queue, queue.Queue), "You must pass a queue from the queue system module"
		self._check_db_version()
		while True:
			list_of_cmds = cmd_queue.get()
			# TODO: implement error handling. Idea: make it return an exception (possible?)
			c = self.conn.cursor()
			for cmd in list_of_cmds:
				try:
					c.execute(cmd[0], cmd[1])
				except IndexError:
					c.execute(cmd[0])
			self.conn.commit()
			result_queue.put(c)
			cmd_queue.task_done()

	def stale_query(self, stale_queue):
		"""This method should only be used for inserting methods,
		as it won't put anything in the result queue"""
		assert isinstance(stale_queue, queue.Queue), "You must pass a queue from the queue system module"
		self._check_db_version()
		while True:
			list_of_cmds = stale_queue.get()
			c = self.conn.cursor()
			for cmd in list_of_cmds:
				try:
					c.execute(cmd[0], cmd[1])
				except IndexError:
					c.execute(cmd[0])
			self.conn.commit()
			stale_queue.task_done()


	def _check_db_version(self):
		"Checks if DB version is allowed. Raises dialog if not"
		if not self.vs_checked:
			vs = "SELECT version FROM version"
			c = self.conn.cursor()
			c.execute(vs)
			db_vs = c.fetchone()
			if db_vs[0] not in db_constants.DB_VERSION:
				msg = "The database is not compatible with the current version of the program"
				exception_handler(msg)
				raise Exception(msg)
			self.vs_checked = True # we have now checked the version for this instance

if __name__ == '__main__':
	raise RuntimeError("Unit tests not yet implemented")
	# unit tests here!