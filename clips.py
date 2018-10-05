import pytube
import watson_developer_cloud as watson
from watson_developer_cloud.speech_to_text_v1 import CustomWord

import logging  # TODO: call basicConfig() on initialization
import json

import io
import os
import time
import re
import collections
from os import environ

from typing import Tuple, List

PLAYLIST_URL = 'https://www.youtube.com/playlist?list=PLiWL8lZPZ2_k1JH6urJ_H7HzH9etwmn7M'
STT_PATH = 'expr/stt/'
CLIPS_PATH = 'yiaygenerator/static/clips/'
MODEL_PATH = 'stt_custom/words.json'

WORD, START, END = 0, 1, 2

stt = watson.SpeechToTextV1(
	username=environ['WATSON_USERNAME'],
	password=environ['WATSON_PASSWORD']
)


def initialize() -> None:
	"""
	Initializes the clips to be used as parts of the final video.
	"""
	for i, url in enumerate(pytube.Playlist(PLAYLIST_URL).parse_links(), start=1):
		update(url, i)


def update(url: str, i: int) -> None:
	"""
	Updates the clips with the contents of a new YIAY video.
	:param url: the video's URL
	:param i: the video's index in the playlist
	:return: None
	"""
	video, audio = download(url, i)
	video.seek(0)
	audio.seek(0)
	
	text, words = speech_to_text(audio, i)


def download(url: str, i: int) -> Tuple[io.BytesIO, io.BytesIO]:
	"""
	Downloads the video from YouTube in two different formats.
	:param url: the video's URL
	:param i: the video's index in the playlist
	:return:
		buffer containing an MP4 file (video + audio),
		and buffer containing a WEBM file (audio only)
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
		logging.exception('Could not download YIAY #%03d', i)


def create_model() -> None:
	"""
	Creates a language model for the speech-to-text service,
	and prints its ID.
	NOTE: should only be used once.
	"""
	print(stt.create_language_model(
		'Jack custom model',
		'en-US_BroadbandModel'
	).get_result()['customization_id'])


def customize_words(*words: CustomWord) -> None:
	model_id = environ['WATSON_CUSTOMIZATION_ID']
	
	stt.add_words(model_id, list(words))
	train(model_id)


def customize_corpus(path: str):
	model_id = environ['WATSON_CUSTOMIZATION_ID']
	
	with open(path) as f:
		stt.add_corpus(
			model_id,
			os.path.basename(path),
			f,
			allow_overwrite=True
		)
	train(model_id)


def train(model_id: str) -> None:
	while stt.get_language_model(model_id).get_result()['status'] != 'ready':
		time.sleep(5)
	stt.train_language_model(model_id)
	
	with open(MODEL_PATH, 'w') as f:
		json.dump(stt.list_words(model_id).get_result(), f, indent='\t')


def speech_to_text(stream: io.BytesIO, i: int) -> Tuple[str, List]:
	"""
	Sends an audio file to the speech-to-text API,
	gets the results and saves them in a JSON file.
	:param stream: audio file binary data
	:param i: the video's index in the playlist
	:return:
		The audio's complete transcript,
		and timestamps for each word.
	"""
	transcript = ''
	timestamps = []
	
	for result in stt.recognize(
		audio=stream,
		content_type='audio/webm',
		customization_id=environ.get('WATSON_CUSTOMIZATION_ID'),  # costs money
		timestamps=True,
		profanity_filter=False
		# TODO: try smart_formatting
	).get_result()['results']:
		
		alternative = result['alternatives'][0]  # only one alternative by default
		
		transcript += alternative['transcript']
		timestamps.extend(alternative['timestamps'])
	
	with open(f'{STT_PATH}{i:03d}.json', 'w') as f:
		json.dump({
			'transcript': transcript,
			'timestamps': timestamps
		}, f, indent='\t')
	
	return transcript, timestamps


PATTERN = (
	r'(?P<intro>.*?asked you )'
	r'(?P<question>.*?)'
	r'(?P<start>(here .*?)?answers )'
	r'(?P<content>.*)'
	r'(?P<outro>leave your answers .*?YIAY )'
	r'(?P<end>.*)'
)


def parse(text: str, timestamps: List[List]):
	# TODO: remove emotions
	match = re.match(PATTERN, text)
	
	'''
	# intro
	part, text = text.split(INTRO, 1)
	count = part.count(' ') + INTRO_COUNT
	
	intro = timestamps[0][START], timestamps[count - 1][END]
	timestamps = timestamps[count:]
	
	# outro
	ind = text.rindex(OUTRO)
	part = text[ind:]
	text = text[:ind]
	count = part.count(' ')
	
	outro = timestamps[-count][START]
	timestamps = timestamps[:-count]
	
	return timestamps, intro, outro
	'''
	

'''
try:
	len(os.listdir)
except FileNotFoundError:
	0

defaultdict
'''
