from typing import ContextManager

import youtube_dl

import contextlib
import os
import io
from logging import info

PLAYLIST_LEN = 453  # this kinda sucks
PLAYLIST_URL = ('https://www.youtube.com/playlist?list=PLiWL8lZPZ2_k1JH6urJ_H7HzH9etwmn7M',)


@contextlib.contextmanager
def video(i: int, only_audio: bool) -> ContextManager[io.BufferedReader]:
	"""
	Downloads a video from YouTube.

	:param i: the video's index in the playlist (counting from 0)
	:param only_audio: True to download only audio, False to download video and audio
	:return: a context manager which returns the video file and removes it on exit.
	"""
	fmt = 'bestaudio[ext=webm]' if only_audio else 'best[ext=mp4]'
	
	info(f'Downloading YIAY #{i:03d} as {"WEBM" if only_audio else "MP4"}...')
	with youtube_dl.YoutubeDL({
			'playlist_items': str(PLAYLIST_LEN + 1 - i),
			'format': fmt,
			'outtmpl': fmt,
			'quiet': True
			# These don't work
			# 'keepvideo': False
			# 'playlistreverse': True
		}) as yt:
		yt.download(PLAYLIST_URL)
	
	file = open(fmt, 'rb')
	try:
		yield file
	finally:
		file.close()
		os.remove(fmt)
