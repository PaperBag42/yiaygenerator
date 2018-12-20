"""Downloads YIAY videos from Youtube."""

from typing import ContextManager

from ._logging import logger

import youtube_dl

import contextlib
import os

PLAYLIST_URL = ('https://www.youtube.com/playlist?list=PLiWL8lZPZ2_k1JH6urJ_H7HzH9etwmn7M',)


@contextlib.contextmanager
def video(i: int, only_audio: bool) -> ContextManager[str]:
	"""
	Downloads a video from YouTube.

	:param i: the video's index in the playlist
	:param only_audio: True to download only audio, False to download video and audio
	:return: a context manager which returns the video file's path and removes it on exit.
	:raise IndexError: if i surpasses the playlist's bounds
	"""
	fmt = 'bestaudio[ext=webm]' if only_audio else 'best[ext=mp4]'
	
	logger.info(f'Downloading {"audio" if only_audio else "video"}...')
	with youtube_dl.YoutubeDL({
		'playlistreverse': True,
		'playlist_items': str(i),
		'format': fmt,
		'outtmpl': fmt,
		'quiet': True,
	}) as yt:
		yt.download(PLAYLIST_URL)
	
	if not os.path.isfile(fmt):
		raise IndexError(i)
	
	try:
		yield fmt
	finally:
		os.remove(fmt)
