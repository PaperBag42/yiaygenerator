import watson_developer_cloud as watson
from watson_developer_cloud.speech_to_text_v1 import CustomWord

import youtube
from youtube import Video

import logging  # TODO: call basicConfig() on initialization
import json

import io
import os
import time
import re
import collections
from os import environ

from typing import Tuple, List

STT_PATH = 'expr/stt/'
CLIPS_PATH = 'expr/clips/'
MODEL_PATH = 'stt_custom/words.json'
LOG_PATH = 'expr/log.csv'


WORD, START, END = 0, 1, 2

stt = watson.SpeechToTextV1(
	username=environ['WATSON_USERNAME'],
	password=environ['WATSON_PASSWORD']
)


def generate(i: int) -> None:
	"""
	Generates clips from a new YIAY video.
	:param i: the video's index in the playlist
	"""
	with Video(i, True) as file:
		text, words = speech_to_text(file, i)


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
	
	with open(path) as file:
		stt.add_corpus(
			model_id,
			os.path.basename(path),
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


def speech_to_text(stream: io.BufferedReader, i: int) -> Tuple[str, List]:
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
	
	with open(f'{STT_PATH}{i:03d}.json', 'w') as file:
		json.dump({
			'transcript': transcript,
			'timestamps': timestamps
		}, file, indent='\t')
	
	return transcript, timestamps


pattern = re.compile(
	r'(?P<intro>.*?asked you )?'  # ok
	r'(?P<question>.*?)'  # ok
	r'(?P<start>(here .*?)?answers )'  # will probably break a lot (he sometimes says "let's go" or other random stuff)
	r'(?P<content>.*)'  # ok
	# TODO: sponsor
	r'(?P<outro>(leave|let) .*?YIAY )'  # ok?
	r'(?P<end>.*)'  # ok
)


def parse(text: str, timestamps: List[List]):
	# TODO: remove emotions
	match = pattern.match(text)
	

'''
try:
	len(os.listdir)
except FileNotFoundError:
	0

defaultdict
'''


def main():
	"""
	Generates all clips to be used as parts of the final video.
	"""
	for i in range(youtube.PLAYLIST_LEN):
		generate(i)


if __name__ == '__main__':
	main()
