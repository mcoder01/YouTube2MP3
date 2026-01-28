import os
import yt_dlp
import requests

from concurrent.futures import ThreadPoolExecutor
from PyQt6.QtGui import QPixmap

class Downloader:
    def __init__(self, max_workers=8):
        self.executor = ThreadPoolExecutor(max_workers)
        self.downloads = {}

    def __submit(self, func, **kwargs):
        return self.executor.submit(func, **kwargs)

    def __progress_callback(self, d):
        if d['status'] == 'downloading':
            downloaded = d.get('downloaded_bytes', 0)
            total = d.get('total_bytes') or d.get('total_bytes_estimate')

            if total:
                percent = downloaded / total * 99.9
                progress_str = f"{percent:.1f}%"
            else:
                progress_str = f"{downloaded / 1E6:.1f} MB"

            link = d['info_dict']['webpage_url']
            self.downloads[link].progressSignal.emit(progress_str)

    def __download_video(self, link, dest):
        ydl_opts = {
            'format': 'bestaudio/best',
            'progress_hooks': [self.__progress_callback],
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
        self.downloads[link].progressSignal.emit("100.0%")

    def __download_thumbnail(self, url, signal):
        data = requests.get(url).content
        thumbnail = QPixmap()
        thumbnail.loadFromData(data)
        signal.emit(thumbnail)

    def get_thumbnail(self, url, signal):
        self.__submit(self.__download_thumbnail, url=url, signal=signal)

    def __download_info(self, link, signal):
        ydl_opts = {'noplaylist': True, 'ignoreerrors': True, 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(link, download=False)
        signal.emit(info)

    def get_info(self, link, signal):
        self.__submit(self.__download_info, link=link, signal=signal)
        
    def submit_video(self, link, output_folder, widget):
        self.downloads[link] = widget
        self.__submit(self.__download_video, link=link, dest=output_folder)

    def shutdown(self):
        self.executor.shutdown(wait=False)