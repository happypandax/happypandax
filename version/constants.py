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

from .database import db
from .gui import app, gui_constants
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QFile
import sys

#IMPORTANT STUFF
def init():
	application = QApplication(sys.argv)
	conn = db.init_db()
	if conn:
		# create log
		try:
			with open('happypanda.log', 'x') as f:
				pass
		except FileExistsError: pass

		DB = db.DBThread(conn)
		WINDOW = app.AppWindow()

		# styling
		d_style = gui_constants.default_stylesheet_path
		u_style =  gui_constants.user_stylesheet_path
	
		if len(u_style) is not 0:
			try:
				style_file = QFile(u_style)
			except:
				style_file = QFile(d_style)
		else:
			style_file = QFile(d_style)

		style_file.open(QFile.ReadOnly)
		style = str(style_file.readAll(), 'utf-8')
		application.setStyleSheet(style)
		sys.exit(application.exec_())
	else:
		from PyQt5.QtWidgets import QMessageBox
		msg_box = QMessageBox()
		msg_box.setInformativeText("The database is not compatible with the current version of the program")
		msg_box.setIcon(QMessageBox.Critical)
		msg_box.setStandardButtons(QMessageBox.Ok)
		msg_box.setDefaultButton(QMessageBox.Ok)
		if msg_box.exec():
			application.exit()
			sys.exit()