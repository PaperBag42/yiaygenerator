from typing import Tuple, List

import youtube

import watson_developer_cloud as watson
from watson_developer_cloud.speech_to_text_v1 import CustomWord

import json
import time
import io
from os import path, environ
from logging import info

STT_PATH = 'expr/stt/'
MODEL_PATH = 'stt_custom/words.json'

stt = watson.SpeechToTextV1(
	username=environ['WATSON_USERNAME'],
	password=environ['WATSON_PASSWORD']
)


def speech_to_text(i: int):
	"""
	Loads the speech-to-text transcript for a YIAY video.
	Makes an API request if a transcript was not found.
	:param i: the video's index in the playlist (counting from 0)
	:return: a full transcript
	"""
	filename = f'{STT_PATH}{i:03d}.json'
	if path.isfile(filename):
		info(f'Loading transcript for YIAY #{i + 1:03d} from {filename}.')
		with open(filename) as file:
			data = json.load(file)
			return data['transcript'], data['timestamps']
	else:
		info(f'Making an API request for YIAY #{i + 1:03d}...')
		with youtube.Video(i, only_audio=True) as file:
			return request(file, filename)


def request(stream: io.BufferedReader, out: str) -> Tuple[str, List]:
	"""
	Sends an audio file to the speech-to-text API,
	gets the results and saves them in a JSON file.
	:param stream: audio file binary data
	:param out: filename to save the result in
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
	).get_result()['results']:
		alternative = result['alternatives'][0]  # only one alternative by default
		
		transcript += alternative['transcript']
		timestamps.extend(alternative['timestamps'])
	
	# save to file
	with open(out, 'w') as file:
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
	print(stt.create_language_model(
		'Jack custom model',
		'en-US_BroadbandModel'
	).get_result()['customization_id'])


def customize_words(*words: CustomWord) -> None:
	model_id = environ['WATSON_CUSTOMIZATION_ID']
	
	stt.add_words(model_id, list(words))
	train(model_id)


def customize_corpus(filename: str):
	model_id = environ['WATSON_CUSTOMIZATION_ID']
	
	with open(filename) as file:
		stt.add_corpus(
			model_id,
			path.basename(filename),
			file,
			allow_overwrite=True
		)
	train(model_id)


def train(model_id: str) -> None:
	while stt.get_language_model(model_id).get_result()['status'] != 'ready':
		time.sleep(5)
	stt.train_language_model(model_id)
	
	with open(MODEL_PATH, 'w') as f:
		json.dump(stt.list_words(model_id).get_result(), f, indent='\t')
