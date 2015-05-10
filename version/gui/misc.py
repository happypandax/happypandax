from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (QWidget, QProgressBar, QLabel,
							 QVBoxLayout, QHBoxLayout)

class Loading(QWidget):
	def __init__(self):
		from ..constants import WINDOW as parent
		super().__init__(parent, Qt.FramelessWindowHint)
		self.widget = QWidget(self)
		self.widget.setStyleSheet("background-color:rgba(0, 0, 0, 0.65)")
		self.progress = QProgressBar()
		self.progress.setStyleSheet("color:white")
		self.text = QLabel()
		self.text.setStyleSheet("color:white;background-color:transparent;")
		layout_ = QHBoxLayout()
		inner_layout_ = QVBoxLayout()
		inner_layout_.addWidget(self.text, 0, Qt.AlignHCenter)
		inner_layout_.addWidget(self.progress)
		self.widget.setLayout(inner_layout_)
		layout_.addWidget(self.widget)
		self.setLayout(layout_)
		self.resize(300,100)
		self.move(
			parent.window().frameGeometry().topLeft() +
			parent.window().rect().center() - self.rect().center())

	def mousePressEvent(self, QMouseEvent):
		pass

	def setText(self, string):
		if string != self.text.text():
			self.text.setText(string)