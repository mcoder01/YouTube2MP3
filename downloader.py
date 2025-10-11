from concurrent.futures import ThreadPoolExecutor
import os

import yt_dlp
import requests
from PyQt6.QtGui import QPixmap

temp_folder = os.environ.get("TEMP") or os.environ.get("TMP") \
    or os.environ.get("TMPDIR") or "/tmp"

class Downloader:
    def __init__(self, max_workers=os.cpu_count()):
        self.executor = ThreadPoolExecutor(max_workers)
        self.downloads = {}

    def submit(self, func, **kwargs):
        return self.executor.submit(func, **kwargs)

    def progress_callback(self, d):
        if d['status'] == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate')

            if total:
                percent = downloaded / total * 100
                progress_str = f"{percent:.1f}%"
            else:
                progress_str = f"{downloaded / 1E6:.1f} MB"

            link = d['info_dict']['webpage_url']
            self.downloads[link].progress.setText(progress_str)

    def download_video(self, link, dest):
        ydl_opts = {
            'format': 'bestaudio/best',
            'progress_hooks': [self.progress_callback],
            'outtmpl': os.path.join(dest, '%(title)s.%(ext)s'),
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '320',
            }],
            'noplaylist': True,
            'ignoreerrors': True,
            'quiet': True
        }
    
        with yt_dlp.YoutubeDL(ydl_opts) as ydl: 
            ydl.download([link])

    def show_info(self, link, info, widget):
        thumbnail_url = info.get('thumbnail')
        if thumbnail_url:
            data = requests.get(thumbnail_url).content
            thumbnail = QPixmap()
            thumbnail.loadFromData(data)
            widget.thumbnail.setPixmap(thumbnail)
        widget.title.setText(info.get("title", link))
        widget.title.setStyleSheet("")

    def get_info(self, link, widget):
        ydl_opts = {'noplaylist': True, 'ignoreerrors': True, 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=False)
            self.show_info(link, info, widget)
        
    def submit_video(self, link, output_folder, widget, info=None):
        if link in self.downloads:
            self.submit(self.download_video, link=link, dest=output_folder)
        else:
            self.downloads[link] = widget
            self.submit(self.download_video, link=link, dest=output_folder)
            if info is None:
                self.submit(self.get_info, link=link, widget=widget)
            else:
                self.show_info(link, info, widget)

    def shutdown(self):
        self.executor.shutdown(wait=False)