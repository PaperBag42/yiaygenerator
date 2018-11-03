import youtube_dl
import os

PLAYLIST_LEN = 452  # this kinda sucks
PLAYLIST_URL = 'https://www.youtube.com/playlist?list=PLiWL8lZPZ2_k1JH6urJ_H7HzH9etwmn7M'


class Video(object):
	"""
	Downloads a video from YouTube.
	:param i: the video's index in the playlist
	:param only_audio: True to download only audio, False to download video and audio
	"""
	def __init__(self, i: int, only_audio: bool):
		self.i = i
		self.fmt = 'webm' if only_audio else 'mp4'
	
	def __enter__(self):
		with youtube_dl.YoutubeDL({
			'playlist_items': str(PLAYLIST_LEN - self.i),
			'format': self.fmt,
			'outtmpl': self.fmt,
			# These don't work
			# 'keepvideo': False
			# 'playlistreverse': True
		}) as yt:
			yt.download([PLAYLIST_URL])
		
		self.f = open(self.fmt, 'rb')
		return self.f
	
	def __exit__(self, *_) -> None:
		"""
		Closes and deletes the file.
		"""
		self.f.close()
		os.remove(self.fmt)
