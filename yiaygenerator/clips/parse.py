from typing import List, Iterable

from .. import homophones
from . import youtube, stt
from .stt import JSON_PATH
from ._logging import logger

import moviepy.video.io.VideoFileClip

import re
import os
import json
import collections

CLIPS_PATH = 'expr/clips/'
LOG_PATH = 'expr/log.csv'


def generate(i: int) -> None:
	"""
	Generates clips from a new YIAY video.
	
	:param i: the video's index in the playlist
	"""
	pass


_pattern = re.compile(
	r'(?P<intro>.*?asked you )?'  # ok
	r'(?P<question>.*?)'  # ok
	r'(?P<start>(here .*?)?answers )?'  # will probably break a lot (he sometimes says "let's go" or other random stuff)
	r'(?P<content>.*)'  # ok
	# TODO: sponsor
	r'(?P<outro>(leave|let) .*?YIAY )'  # ok?
	r'(?P<end>.*)'  # ok
)


def parse(text: str, timestamps: List[List]):
	match = _pattern.match(text)


def write(i: int, timestamps: List[List]) -> None:
	count = collections.Counter()
	
	with youtube.video(i, only_audio=False) as video:
		with moviepy.video.io.VideoFileClip.VideoFileClip(video) as clip:
			
			logger.info(f'Writing {len(timestamps)} clips...')
			for word, start, end in timestamps:
				dirname = (
					f'{CLIPS_PATH}/'
					f'{word if word.startswith("%") else homophones.get_homophone(word)}/'
				)
				if not os.path.isdir(dirname):
					os.mkdir(dirname)
				
				clip.subclip(start, end).write_videofile(
					f'{dirname}/{i:03d}-{count[word]:03d}.mp4',
					verbose=False, progress_bar=False
				)
				count[word] += 1
		
	with open(f'{JSON_PATH}/{i:03d}.json', 'r+') as file:
		data = json.load(file)
		file.seek(0)
		file.truncate()
		json.dump({**data, 'parsed': True}, file)


def _test(inds: Iterable[int]) -> None:
	"""
	Tests the RegEx pattern against a range of YIAY videos.
	
	:param inds: indexes of videos to test
	"""
	matched = 0
	total = 0
	for i in inds:
		logger.ind = i
		total += 1
		
		text = stt.speech_to_text(i)[1]
		match = _pattern.match(text)
		
		if match is None:
			logger.error('RegEx match failed.')
			continue
		
		matched += 1
		for name, part in match.groupdict().items():
			if part is None:
				logger.warning(f'Group %{name} was not captured.')
				continue
			
			logger.info(f'Group %{name}: {100 * len(part) / len(text):.2f}% of video.')
	logger.info(f'Matched {matched}/{total} videos.')


def _reset():
	"""Deletes the clips and resets the 'parsed' attribute in the JSON files."""
	if input('ARE YOU SURE ABOUT THAT [Y/N]') != 'N':  # just making sure
		for *_, names in os.walk(CLIPS_PATH):
			for name in names:
				os.remove(name)
		
		for name in os.listdir(JSON_PATH):
			with open(name, 'r+') as file:
				data = json.load(file)
				file.seek(0)
				file.truncate()
				json.dump({**data, 'parsed': False}, file)


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
