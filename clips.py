import pytube
import logging

PLAYLIST_URL = 'https://www.youtube.com/playlist?list=PLiWL8lZPZ2_k1JH6urJ_H7HzH9etwmn7M'
CLIPS_PATH = 'yiaygenerator/static/clips'
TEMP_FILENAME = 'tmp'


def initialize() -> None:
	"""
	Initializes the clips to be used as parts of the final video.
	"""
	for url in pytube.Playlist(PLAYLIST_URL).parse_links():
		update(url)


def update(url: str) -> None:
	"""
	Updates the clips with the contents of a new YIAY video.
	:param url: the video's URL
	:return: None
	"""
	file_path = download(url)
	print(file_path)


def download(url: str) -> str:
	"""
	Downloads the video from YouTube.
	:param url: the video's URL
	:return: path to the video file
	"""
	try:
		return pytube.YouTube(url).streams.filter(
			progressive=True,
			subtype='mp4'
		).first().download(filename=TEMP_FILENAME)
		
	except pytube.exceptions.PytubeError:
		logging.exception('Could not download video')
