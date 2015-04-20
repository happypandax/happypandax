import sys
from PyQt5.QtWidgets import QApplication, QWidget
from PyQt5.QtGui import QIcon

class WindowsError(QWidget):

    def __init__(self):
        super().__init__()

        self.initUI()

    def initUI(self):

        self.setGeometry(300, 300, 300, 220)
        self.setWindowTitle('Hello World')
        #self.setWindowIcon(QIcon(#5r675))

if __name__ == '__main__':
    app = QApplication(sys.argv)

    w = QWidget()
    w.resize(100,50)
    w.move(100,100)
    w.setWindowTitle('Hello World')
    w.show()

    sys.exit(app.exec_())
