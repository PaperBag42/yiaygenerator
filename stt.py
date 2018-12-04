from typing import Tuple, List, Dict, Iterable, Generator

import youtube

import watson_developer_cloud as watson
from watson_developer_cloud.speech_to_text_v1 import CustomWord

import json
import time
import io
from os import path, environ

import logging
from logging import info

STT_PATH = 'expr/stt/'
MODEL_PATH = 'stt_custom/words.json'

service = watson.SpeechToTextV1(
	username=environ['WATSON_USERNAME'],
	password=environ['WATSON_PASSWORD']
)
# TODO: would be cool if I registered a callback here


def speech_to_text(inds: Iterable[int]) -> Generator[Tuple[int, str, List]]:
	"""
	Loads speech-to-text transcripts for a list of YIAY videos.
	Makes an API request for each transcript that was not found.

	:param inds: the video's index in the playlist
	:return: a tuple containing an index, a full transcript and word timestamps for each video.
	"""
	ids = {}
	for i in inds:
		filename = f'{STT_PATH}{i:03d}.json'
		if path.isfile(filename):
			info(f'Loading transcript for YIAY #{i:03d} from {filename}.')
			with open(filename) as file:
				data = json.load(file)
				yield i, data['transcript'], data['timestamps']
		else:
			with youtube.video(i, only_audio=True) as file:
				ids[request(file, i)] = i
	
	yield from resolve(ids)


def request(stream: io.BufferedReader, i: int) -> str:
	"""
	Sends an audio file to the speech-to-text API.

	:param stream: audio file binary data
	:param i: the video's index in the playlist
	:return: the created job's ID.
	"""
	try:
		info(f'Making an API request for YIAY #{i:03d}...')
		return service.create_job(
				audio=stream,
				content_type='audio/webm',
				language_customization_id=environ.get('WATSON_CUSTOMIZATION_ID'),  # costs money
				timestamps=True,
				profanity_filter=False
			).get_result()['id']
		
	except watson.WatsonApiException:  # TODO: get response from support
		logging.warning(f'YIAY #{i:03d}: Got the weird error again, retrying...')
		stream.seek(0)
		time.sleep(5)
		
		return request(stream, i)


def resolve(ids: Dict[int]) -> Generator[Tuple[int, str, List]]:
	"""
	Waits for created jobs to complete, and fetches their responses.
	
	:param ids: a dict mapping each job ID to the index of the video it is working on
	:return: index, transcript and timestamps for each job resolved
	"""
	pass


def process(i: int, response: Dict) -> Tuple[int, str, List]:
	"""
	Processes the response from a completed job.
	Saves the relevant data in a JSON file.
	
	:param i: the video's index in the playlist
	:param response: response from a completed job
	:return: index, transcript and word timestamps
	"""
	transcript = ''
	timestamps = []
	
	for result in response['results']:
		alternative = result['alternatives'][0]  # only one alternative by default
		
		transcript += alternative['transcript']
		timestamps.extend(alternative['timestamps'])
	
	# save to file
	with open(f'{STT_PATH}{i:03d}.json', 'w') as file:
		json.dump({
			# 'i': i,
			'transcript': transcript,
			'timestamps': timestamps
		}, file, indent='\t')
	
	return i, transcript, timestamps


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
