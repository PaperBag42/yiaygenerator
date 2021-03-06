"""
Fetches text-to-speech transcripts of videos
from the IBM Watson developer cloud API.
"""

from typing import Tuple, List, Dict, BinaryIO, NamedTuple

from . import youtube
from ._logging import logger

import watson_developer_cloud as watson
from watson_developer_cloud.watson_service import requests
from watson_developer_cloud.speech_to_text_v1 import CustomWord

import json
import time
from os import environ, PathLike
from pathlib import Path

json_path = Path('expr/stt/')
model_path = Path('stt_custom/')

_service = watson.SpeechToTextV1(
	username=environ['WATSON_USERNAME'],
	password=environ['WATSON_PASSWORD']
)


class Timestamp(NamedTuple):
	"""Word timestamp as received from the API."""
	word: str
	start: float
	end: float


def speech_to_text(i: int) -> Tuple[bool, str, List[Timestamp]]:
	"""
	Loads the speech-to-text transcript for a YIAY video.
	Makes an API request if a transcript was not found.
	
	:param i: the video's index in the playlist
	:return:
		A boolean indicating whether the video was already parsed,
		a full transcript, and timestamps for each word.
	"""
	path = json_path / f'{i:03d}.json'
	if path.exists():
		logger.debug(f'Loading transcript from {path}.')
		with open(path) as file:
			data = json.load(file)
		return data['clipped'], data['transcript'], [Timestamp(*s) for s in data['timestamps']]
	else:
		with youtube.video(i, only_audio=True) as audio:
			return (False, *_process(path, _request(audio)))


def _request(stream: BinaryIO) -> Dict:
	"""
	Sends an audio file to the speech-to-text API,
	and gets the results.
	
	:param stream: audio file binary data
	:return:
		The audio's complete transcript,
		and timestamps for each word.
	"""
	logger.info(f'Making an API request...')
	try:
		return _service.recognize(
			audio=stream,
			content_type='audio/webm',
			language_customization_id=environ.get('WATSON_CUSTOMIZATION_ID'),  # costs money
			timestamps=True,
			profanity_filter=False
		).get_result()
	
	except (watson.WatsonApiException, requests.exceptions.ConnectionError) as e:
		logger.warning(f'Got the weird {e.__class__.__name__} again, retrying...')
		
		stream.seek(0)
		time.sleep(5)
		return _request(stream)


def _process(filename: PathLike, response: Dict) -> Tuple[str, List[Timestamp]]:
	"""
	Collects the relevant data from an API response,
	and saves it in a JSON file.
	
	:param filename: path to a file to save the data in
	:param response: the response from an API request for an audio file
	:return:
		The audio's complete transcript,
		and timestamps for each word.
	"""
	transcripts = []
	timestamps = []
	
	for result in response['results']:
		alternative = result['alternatives'][0]  # only one alternative by default
		
		transcripts.append(alternative['transcript'])
		timestamps.extend(alternative['timestamps'])
	
	transcript = ''.join(transcripts)
	# save to file
	with open(filename, 'w') as file:
		json.dump({
			'clipped': False,
			'transcript': transcript,
			'timestamps': timestamps
		}, file, separators=(',', ':'))
	
	return transcript, [Timestamp(*s) for s in timestamps]


def model_setup() -> str:
	"""
	Sets up a language model for the speech-to-text service,
	and returns its ID.
	NOTE: should only be used once.
	"""
	model_id = _service.create_language_model(
		'Jack custom model',
		'en-US_BroadbandModel'
	).get_result()['customization_id']
	
	_service.add_words(model_id, [
		CustomWord('finna', ['Finnan', 'Finno']),
		CustomWord('YIAY', ['yeah I', 'yeah I.']),
		CustomWord('answers', ['cancers']),
	])
	
	filename = model_path / 'outro.txt'
	with open(filename) as file:
		_service.add_corpus(model_id, filename.name, file)
	
	while _service.get_language_model(model_id).get_result()['status'] != 'ready':
		time.sleep(5)
	_service.train_language_model(model_id)
	
	with open(model_path / 'words.json', 'w') as file:
		json.dump(_service.list_words(model_id).get_result(), file, indent='\t')
	
	return model_id
