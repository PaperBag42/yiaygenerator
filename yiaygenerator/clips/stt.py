from typing import Tuple, List, Dict

from . import youtube
from ._logging import logger

import requests
import watson_developer_cloud as watson
from watson_developer_cloud.speech_to_text_v1 import CustomWord

import io
import json
import time
from time import sleep
from os import path, environ

STT_PATH = 'expr/stt/{ind:03d}.json'
MODEL_PATH = 'stt_custom/words.json'

service = watson.SpeechToTextV1(
		username=environ['WATSON_USERNAME'],
		password=environ['WATSON_PASSWORD']
)


def speech_to_text(i: int) -> Tuple[str, List]:
	"""
	Loads the speech-to-text transcript for a YIAY video.
	Makes an API request if a transcript was not found.
	
	:param i: the video's index in the playlist
	:return: a full transcript, and timestamps for each word
	"""
	logger.ind = i
	filename = STT_PATH.format(ind=i)
	if path.isfile(filename):
		logger.info(f'Loading transcript from {filename}.')
		with open(filename) as file:
			data = json.load(file)
			return data['transcript'], data['timestamps']
	else:
		with youtube.video(i, only_audio=True) as file:
			return _process(filename, request(file))


def request(stream: io.BufferedReader) -> Dict:
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
		return service.recognize(
				audio=stream,
				content_type='audio/webm',
				language_customization_id=environ.get('WATSON_CUSTOMIZATION_ID'),  # costs money
				timestamps=True,
				profanity_filter=False
			).get_result()
	
	except (watson.WatsonApiException, requests.exceptions.ConnectionError) as e:
		logger.warning(f'Got the weird {e.__class__.__name__} again, retrying...')
		
		stream.seek(0)
		sleep(5)
		return request(stream)


def _process(filename: str, response: Dict) -> Tuple[str, List]:
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
				'transcript': transcript,
				'timestamps': timestamps
			}, file, indent='\t')
	
	return transcript, timestamps


# -- Customization --

def create_model() -> None:
	"""
	Creates a language model for the speech-to-text service,
	and prints its ID.
	NOTE: should only be used once.
	"""
	print(service.create_language_model(
			'Jack custom model',
			'en-US_BroadbandModel'
		).get_result()['customization_id'])


def customize_words(*words: CustomWord) -> None:
	model_id = environ['WATSON_CUSTOMIZATION_ID']
	
	service.add_words(model_id, list(words))
	train(model_id)


def customize_corpus(filename: str):
	model_id = environ['WATSON_CUSTOMIZATION_ID']
	
	with open(filename) as file:
		service.add_corpus(
				model_id,
				path.basename(filename),
				file,
				allow_overwrite=True
			)
	train(model_id)


def train(model_id: str) -> None:
	while service.get_language_model(model_id).get_result()['status'] != 'ready':
		time.sleep(5)
	service.train_language_model(model_id)
	
	with open(MODEL_PATH, 'w') as f:
		json.dump(service.list_words(model_id).get_result(), f, indent='\t')
