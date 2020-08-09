import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QSize, pyqtSlot
from PyQt5.QtGui import QImage, QPalette, QBrush, QIcon, QFont
from PyQt5.QtWidgets import *
from complete_model import on_image, on_video


class MainWindow(QMainWindow):
    WIDTH = 1200
    HEIGHT = 800

    def __init__(self, *args, **kwargs):
        super(MainWindow, self).__init__(*args, **kwargs)

        self.initGUI()

    def initGUI(self):
        self.setWindowTitle("Face mask detection")
        self.setFixedSize(MainWindow.WIDTH, MainWindow.HEIGHT)
        self.setWindowIcon(QIcon('icon.png'))

        self.set_background()

        title = QLabel('Face mask detection', self)
        titleFont = QFont('Arial', 50)
        titleFont.setBold(True)
        title.setFont(titleFont)
        title.adjustSize()
        title.move(round(MainWindow.WIDTH / 2 - title.width() / 2), 100)
        
        button = QPushButton('Load image or video', self)
        button.setAutoFillBackground(True)
        # button.setStyleSheet("background-color : yellow")
        buttonFont = QFont('Arial', 20)
        button.setFont(buttonFont)
        button.adjustSize() 
        button.setToolTip('Choose file on which you want to label faces with and without masks')
        button.move(round(MainWindow.WIDTH / 2 - button.width() / 2), 500)
        button.clicked.connect(self.load)

    def set_background(self):
        oImage = QImage("back.png")
        sImage = oImage.scaled(QSize(1200, 800))
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(sImage))                        
        self.setPalette(palette)

    @pyqtSlot()
    def load(self):
        file, _ = QFileDialog(self).getOpenFileName(self, "Open file", "", "All files (*.*);;JPEG (*.jpg *.jpeg)")
        
        if not file:
            return

        filename, file_extension = os.path.splitext(file)
        
        if file_extension == '.mp4':
            on_video(file)
        else:
            on_image(file)

def window():
    app = QApplication(sys.argv)
    win = MainWindow()

    win.show()

    sys.exit(app.exec_())


if __name__ == '__main__':
    window()