import pytube
import logging
import watson_developer_cloud as watson
import io
import os
from os import environ

from typing import Tuple, List

PLAYLIST_URL = 'https://www.youtube.com/playlist?list=PLiWL8lZPZ2_k1JH6urJ_H7HzH9etwmn7M'
CLIPS_PATH = 'yiaygenerator/static/clips'

stt = watson.SpeechToTextV1(
	username=environ['WATSON_USERNAME'],
	password=environ['WATSON_PASSWORD']
)


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
	video, audio = download(url)
	video.seek(0)
	audio.seek(0)
	
	text, words = speech_to_text(audio)


def download(url: str) -> Tuple[io.BytesIO, io.BytesIO]:
	"""
	Downloads the video from YouTube in two different formats.
	:param url: the video's URL
	:return:
		path to an MP4 file (video + audio),
		and path to a WEBM file (audio only)
	"""
	try:
		streams = pytube.YouTube(url).streams
		return (
			streams.filter(
				progressive=True,
				subtype='mp4'
			).first().stream_to_buffer(),
			streams.filter(
				only_audio=True,
				subtype='webm'
			).first().stream_to_buffer()
		)
		
	except pytube.exceptions.PytubeError:
		logging.exception('Could not download video')


def speech_to_text(stream: io.BytesIO) -> Tuple[str, List]:
	"""
	Sends an audio file to the speech-to-text API
	and gets the results.
	:param stream: audio file binary data
	:return:
		The audio's complete transcript,
		and timestamps for each word.
	"""
	transcripts = ''
	timestamps = []
	
	for result in stt.recognize(
		audio=stream,
		content_type='audio/webm',
		customization_id=environ.get('WATSON_CUSTOMIZATION_ID'),  # costs money
		timestamps=True
		# TODO: try smart_formatting
	).get_result()['results']:
		
		alternative = result['alternatives'][0]  # only one alternative by default
		
		transcripts += alternative['transcript']
		timestamps.extend(alternative['timestamps'])

	return transcripts, timestamps


'''
try:
	len(os.listdir)
except FileNotFoundError:
	0
'''