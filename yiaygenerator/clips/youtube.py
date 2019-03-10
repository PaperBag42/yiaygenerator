"""Downloads YIAY videos from Youtube."""

from typing import BinaryIO

from ._logging import logger

import youtube_dl

import tempfile
import contextlib
from pathlib import Path

PLAYLIST_URL = 'https://www.youtube.com/playlist?list=PLiWL8lZPZ2_k1JH6urJ_H7HzH9etwmn7M',
cache_path = Path('expr/cache')


def video(i: int, only_audio: bool) -> BinaryIO:
	"""
	Downloads a video from YouTube.
	If the video cannot be downloaded, tries to get it from a cache directory.

	:param i: the video's index in the playlist
	:param only_audio: True to download only audio, False to download video and audio
	:return: a temporary file containing the file
	:raise IndexError: if i surpasses the playlist's bounds
	:raise DownloadError: if a YouTube server side error occurs
	"""
	ext = '.webm' if only_audio else '.mp4'
	
	path = cache_path / f'{i:03d}{ext}'
	if path.exists():
		logger.info(f'Loading {path}...')
		return open(path, 'rb')
	
	f = tempfile.NamedTemporaryFile(suffix=ext)
	
	logger.info(f'Downloading {"audio" if only_audio else "video"}...')
	with youtube_dl.YoutubeDL({
		'quiet': True,
		'playlistreverse': True,
		'playlist_items': str(i),
		'format': 'bestaudio[ext=webm]' if only_audio else 'best[ext=mp4]',
		'outtmpl': '-',
	}) as yt:
		with contextlib.redirect_stdout(f):
			yt.download(PLAYLIST_URL)
	
	if f.tell() == 0:
		raise IndexError(i)
	
	f.seek(0)
	return f
