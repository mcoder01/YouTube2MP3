import os
import sys

from PyQt6.QtWidgets import QMainWindow, QApplication, QGraphicsOpacityEffect, QFileDialog, QWidget
from PyQt6.QtGui import QIcon, QPixmap
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6 import uic

import yt_dlp
from downloader import Downloader

downloader = Downloader()

def setVisible(widget, visible):
    effect = widget.graphicsEffect()
    if effect is None or not isinstance(effect, QGraphicsOpacityEffect):
        effect = QGraphicsOpacityEffect()

    effect.setOpacity(1 if visible else 0)
    widget.setGraphicsEffect(effect)

class DlItem(QWidget):
    infoSignal = pyqtSignal(dict)
    progressSignal = pyqtSignal(str)
    thumbnailSignal = pyqtSignal(QPixmap)

    def __init__(self, link, **kwargs):
        super().__init__(**kwargs)
        uic.loadUi("list_item.ui", self)

        self.link = link
        self.infoSignal.connect(self.show_info)
        self.progressSignal.connect(self.progress.setText)
        self.thumbnailSignal.connect(self.show_thumbnail)

    def show_info(self, info):
        thumbnail_url = info.get('thumbnail')
        if thumbnail_url:
            downloader.get_thumbnail(thumbnail_url, self.thumbnailSignal)
        self.title.setText(info.get("title", self.link))
        self.title.setStyleSheet("")

    def show_thumbnail(self, thumbnail):
        self.thumbnail.setPixmap(thumbnail)

class Converter(QMainWindow):
    urlInfoSignal = pyqtSignal(dict)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        uic.loadUi("gui.ui", self)

        setVisible(self.dlSection, False)
        self.output_folder = os.path.join(os.environ['USERPROFILE'], 'Music')
        self.urlInfoSignal.connect(self.start_conversions)

    def chooseFolder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select the download folder...", self.output_folder)
        if folder:
            self.output_folder = folder

    def convert_video(self, id, info=None):
        link = f"https://www.youtube.com/watch?v={id}"
        if link in downloader.downloads:
            item = downloader.downloads[link]
            item.progress.setText("0.0%")
        else:
            item = DlItem(link)
            self.dlList.layout().insertWidget(0, item)

        if info:
            item.show_info(info)
        else:
            downloader.get_info(link, item.infoSignal)
        downloader.submit_video(link, self.output_folder, item)

    def start_conversions(self, info):
        if info.get('_type') == "playlist":
            for entry in info['entries']:
                if entry.get("id"):
                    self.convert_video(entry['id'])
        else:
            self.convert_video(info['id'], info)
        self.convertBtn.setEnabled(True)
        QApplication.restoreOverrideCursor()

    def convert(self):
        link = self.link.text()
        if len(link) == 0:
            return
        
        self.convertBtn.setEnabled(False)
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        os.makedirs(self.output_folder, exist_ok=True)
        setVisible(self.dlSection, True)
        downloader.get_info(link, self.urlInfoSignal)

if __name__ == "__main__":
    try:
        yt_dlp.update()
    except:
        pass

    window = QApplication(sys.argv)
    app = Converter()
    app.setWindowIcon(QIcon("logo.ico"))
    app.show()
    sys.exit(window.exec())