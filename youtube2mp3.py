import os
import sys

from PyQt6.QtWidgets import QMainWindow, QApplication, QGraphicsOpacityEffect, QFileDialog, QWidget
from PyQt6.QtGui import QIcon
from PyQt6 import uic

import yt_dlp
from downloader import Downloader

def setVisible(widget, visible):
    effect = widget.graphicsEffect()
    if effect is None or not isinstance(effect, QGraphicsOpacityEffect):
        effect = QGraphicsOpacityEffect()

    effect.setOpacity(1 if visible else 0)
    widget.setGraphicsEffect(effect)

class DlItem(QWidget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        uic.loadUi("list_item.ui", self)

class Converter(QMainWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        uic.loadUi("gui.ui", self)

        setVisible(self.dlSection, False)
        self.output_folder = os.path.join(os.environ['USERPROFILE'], 'Music')
        self.downloader = Downloader()

    def chooseFolder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select the download folder...", self.output_folder)
        if folder:
            self.output_folder = folder

    def convert_video(self, id, info=None):
        link = f"https://www.youtube.com/watch?v={id}"
        if link in self.downloader.downloads:
            item = self.downloader.downloads[link]
            item.progress.setText("0.0%")
        else:
            item = DlItem()
            self.dlList.layout().insertWidget(0, item)
        self.downloader.submit_video(link, self.output_folder, item, info)

    def convert(self):
        link = self.link.text()
        if len(link) == 0:
            return
        
        os.makedirs(self.output_folder, exist_ok=True)
        setVisible(self.dlSection, True)

        ydl_opts = {'ignoreerrors': True, 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=False)
            if info.get('_type') == "playlist":
                for entry in info['entries']:
                    if entry.get("id"):
                        self.convert_video(entry['id'])
            else:
                self.convert_video(info['id'], info)

if __name__ == "__main__":
    window = QApplication(sys.argv)
    app = Converter()
    app.setWindowIcon(QIcon("logo.ico"))
    app.show()
    sys.exit(window.exec())