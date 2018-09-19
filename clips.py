from typing import Tuple

import pytube
import logging
import watson_developer_cloud as watson
from os import environ

import json

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
	mp4, webm = download(url)
	print(mp4, webm)


def download(url: str) -> Tuple[str, str]:
	"""
	Downloads the video from YouTube.
	:param url: the video's URL
	:return: path to the video file
	"""
	try:
		streams = pytube.YouTube(url).streams
		return (
			streams.filter(
				progressive=True,
				subtype='mp4'
			).first().download(filename='video'),
			streams.filter(
				only_audio=True,
				subtype='webm'
			).first().download(filename='audio')
		)
		
	except pytube.exceptions.PytubeError:
		logging.exception('Could not download video')


def speech_to_text(file_path: str) -> None:
	with open(file_path, 'rb') as f, open('result.json', 'w') as out:
		out.write(json.dumps(
			watson.SpeechToTextV1(
				username=environ['WATSON_USERNAME'],
				password=environ['WATSON_PASSWORD']
			).recognize(
				audio=f,
				content_type='audio/webm',
				timestamps=True
			).get_result(),
			indent=2
		))
