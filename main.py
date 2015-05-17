#NOTE: import like this: version.parent.childs
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QFile
from sys import argv, exit
import os

if __name__ == '__main__':
	from version.gui.gui_constants import default_stylesheet_path as d_style
	from version.gui.gui_constants import user_stylesheet_path as u_style
	
	if len(u_style) is not 0:
		try:
			style_file = QFile(u_style)
		except:
			style_file = QFile(d_style)
	else:
		style_file = QFile(d_style)

	style_file.open(QFile.ReadOnly)
	style = str(style_file.readAll(), 'utf-8')

	app = QApplication(argv)
	from version.constants import WINDOW
	app.setStyleSheet(style)
	exit(app.exec_())