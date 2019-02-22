"""Downloads YIAY videos from Youtube."""

from ._logging import logger

import youtube_dl
from youtube_dl.utils import DownloadError

import contextlib
from pathlib import Path
from os import PathLike

PLAYLIST_URL = 'https://www.youtube.com/playlist?list=PLiWL8lZPZ2_k1JH6urJ_H7HzH9etwmn7M',
cache_path = Path('expr/cache')


@contextlib.contextmanager
def video(i: int, only_audio: bool) -> PathLike:
	"""
	Downloads a video from YouTube.
	If the video cannot be downloaded, tries to get it from a cache directory.

	:param i: the video's index in the playlist
	:param only_audio: True to download only audio, False to download video and audio
	:return: a context manager which returns the video file's path and removes it on exit
	:raise IndexError: if i surpasses the playlist's bounds
	:raise DownloadError: if a YouTube server side error occurs
	"""
	path = Path(f'{i:03d}.{"webm" if only_audio else "mp4"}')
	
	logger.info(f'Downloading {"audio" if only_audio else "video"}...')
	with youtube_dl.YoutubeDL({
		'quiet': True,
		'playlistreverse': True,
		'playlist_items': str(i),
		'format': 'bestaudio[ext=webm]' if only_audio else 'best[ext=mp4]',
		'outtmpl': str(path),
	}) as yt:
		try:
			yt.download(PLAYLIST_URL)
		except DownloadError:
			path = cache_path / path
			if not path.exists():
				logger.error('Youtube failed to provide video')
	
	if not path.exists():
		raise IndexError(i)
	
	try:
		yield path
	finally:
		if path.parent != cache_path:
			try:
				path.unlink()
			except PermissionError:
				logger.error('Failed to remove file')
