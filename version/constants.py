"""
This file is part of Happypanda.
Happypanda is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 2 of the License, or
any later version.
Happypanda is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.
You should have received a copy of the GNU General Public License
along with Happypanda.  If not, see <http://www.gnu.org/licenses/>.
"""

from .database import db, db_constants
from .gui import app, gui_constants
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QFile
import sys, logging, os, argparse

#IMPORTANT STUFF
def start():

	parser = argparse.ArgumentParser(prog='Happypanda',
								  description='A manga/doujinshi manager with tagging support')
	parser.add_argument('-d', '--debug', action='store_true',
					 help='happypanda_debug_log.log will be created in main directory')
	parser.add_argument('-v', '--version', action='version',
					 version='Happypanda v{}'.format(gui_constants.vs))

	args = parser.parse_args()
	if args.debug:
		print("happypanda_debug.log created at {}".format(os.getcwd()))
		# create log
		try:
			with open('happypanda_debug.log', 'x') as f:
				pass
		except FileExistsError:
			pass

		logging.basicConfig(level=logging.DEBUG,
						format='%(asctime)-8s %(levelname)-6s %(name)-6s %(message)s',
						datefmt='%d-%m %H:%M',
						filename='happypanda_debug.log',
						filemode='w')
	else:
		try:
			with open('happypanda.log', 'x') as f:
				pass
		except FileExistsError: pass

		logging.basicConfig(level=logging.INFO,
						format='%(asctime)-8s %(levelname)-6s %(name)-6s %(message)s',
						datefmt='%d-%m %H:%M',
						filename='happypanda.log',
						filemode='a')


	log = logging.getLogger(__name__)
	log_i = log.info
	log_d = log.debug
	log_w = log.warning
	log_e = log.error
	log_c = log.critical

	application = QApplication(sys.argv)
	log_d('Happypanda Version {}'.format(gui_constants.vs))
	log_d('App Event Start: OK')
	try:
		conn = db.init_db()
		log_d('Init DB Conn: OK')
	except:
		log_d('Database connection failed')
		from PyQt5.QtGui import QIcon
		from PyQt5.QtWidgets import QMessageBox
		log_i('Invalid database')
		msg_box = QMessageBox()
		msg_box.setWindowIcon(QIcon(gui_constants.APP_ICO_PATH))
		msg_box.setText('Invalid database')
		msg_box.setInformativeText("Do you want to create a new database?")
		msg_box.setIcon(QMessageBox.Critical)
		msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
		msg_box.setDefaultButton(QMessageBox.Yes)
		if msg_box.exec() == QMessageBox.Yes:
			pass
		else:
			application.exit()
			log_d('Normal Exit App: OK')
			sys.exit()

	def start_main_window(conn):
		DB = db.DBThread(conn)
		WINDOW = app.AppWindow()

		# styling
		d_style = gui_constants.default_stylesheet_path
		u_style =  gui_constants.user_stylesheet_path
	
		if len(u_style) is not 0:
			try:
				style_file = QFile(u_style)
				log_i('Select userstyle: OK')
			except:
				style_file = QFile(d_style)
				log_i('Select defaultstyle: OK')
		else:
			style_file = QFile(d_style)
			log_i('Select defaultstyle: OK')

		style_file.open(QFile.ReadOnly)
		style = str(style_file.readAll(), 'utf-8')
		application.setStyleSheet(style)
		try:
			os.mkdir('temp')
		except FileExistsError:
			try:
				for root, dirs, files in os.walk('temp', topdown=False):
					for name in files:
						os.remove(os.path.join(root, name))
					for name in dirs:
						os.rmdir(os.path.join(root, name))
			except:
				log_d('Empty temp: FAIL')
		log_d('Create temp: OK')

		sys.exit(application.exec_())

	def db_upgrade():
		log_d('Database connection failed')
		from PyQt5.QtGui import QIcon
		from PyQt5.QtWidgets import QMessageBox

		msg_box = QMessageBox()
		msg_box.setWindowIcon(QIcon(gui_constants.APP_ICO_PATH))
		msg_box.setText('Incompatible database!')
		msg_box.setInformativeText("Do you want to upgrade to newest version?" +
							 "Don't worry about your data. It'll remain mostly the same.")
		msg_box.setIcon(QMessageBox.Critical)
		msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
		msg_box.setDefaultButton(QMessageBox.Yes)
		if msg_box.exec() == QMessageBox.Yes:
			import threading
			db_p = db_constants.DB_PATH
			threading.Thread(target=db.add_db_revisions,
					args=(db_p,)).start()
			done = None
			while not done:
				done = db.ResultQueue.get()
			conn = db.init_db()
			start_main_window(conn)
		else:
			application.exit()
			log_d('Normal Exit App: OK')
			sys.exit()

	if conn:
		start_main_window(conn)
	else:
		db_upgrade()