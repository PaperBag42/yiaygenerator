import youtube_dl
import os
from logging import info

PLAYLIST_LEN = 453  # this kinda sucks
PLAYLIST_URL = ('https://www.youtube.com/playlist?list=PLiWL8lZPZ2_k1JH6urJ_H7HzH9etwmn7M',)


class Video(object):
	"""
	Downloads a video from YouTube.
	:param i: the video's index in the playlist (counting from 0)
	:param only_audio: True to download only audio, False to download video and audio
	"""
	def __init__(self, i: int, only_audio: bool):
		self.fmt = 'bestaudio[ext=webm]' if only_audio else 'best[ext=mp4]'
		self.opts = {
			'playlist_items': str(PLAYLIST_LEN - i),  # start counting from 0
			'format': self.fmt,
			'outtmpl': self.fmt,
			'quiet': True
			# These don't work
			# 'keepvideo': False
			# 'playlistreverse': True
		}
		info(f'Downloading YIAY #{i + 1:03d} as {"WEBM" if only_audio else "MP4"}...')
	
	def __enter__(self):
		with youtube_dl.YoutubeDL(self.opts) as yt:
			yt.download(PLAYLIST_URL)
		
		self.file = open(self.fmt, 'rb')
		return self.file
	
	def __exit__(self, *_) -> None:
		"""
		Closes and deletes the file.
		"""
		self.file.close()
		os.remove(self.fmt)
