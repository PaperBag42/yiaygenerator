"""Generates video clips using the speech-to-text results."""

from typing import List, Iterable

from .. import homophones
from . import youtube, stt
from .stt import Timestamp, JSON_PATH
from ._logging import logger

import moviepy.video.io.VideoFileClip

import re
import os
import json
import collections

CLIPS_PATH = 'expr/clips/'
LOG_PATH = 'expr/log.csv'


def create() -> None:
	"""
	Creates video clips from all YIAY videos.
	"""
	i = 1
	while True:
		logger.ind = i
		try:
			clipped, text, timestamps = stt.speech_to_text(i)
		except IndexError:
			break
		
		if not clipped and _group(text, timestamps):  # don't use videos that don't match
			_write(i, timestamps)
		
		i += 1


_pattern = re.compile(
	r'(?P<INTRO>.*? asked you )?'
	r'.*? '
	r'(?P<START>(here .*? )?answers )?'  # will probably break a lot (he sometimes says "let's go" or other random stuff)
	r'.* '
	# TODO: sponsor
	r'(?P<OUTRO>(leave|let) .*? YIAY )'
	# r'(?P<END>.*? episode )'
	r'.* '
)


def _group(text: str, timestamps: List[Timestamp]) -> bool:
	"""
	Tries to detect parts of the video that are typical
	for a YIAY video.
	Groups the detected parts into single clips in the timestamp list.
	
	:param text: the video's full transcript to be matched against a RegEx pattern
	:param timestamps: the timestamps list to be modified
	:return: true if the match succeeded
	"""
	match = _pattern.fullmatch(text)
	if match is None:
		logger.error('RegEx match failed.')
		return False
	
	diff = 0
	for group, sub in match.groupdict().items():
		if not sub:  # empty or None
			logger.warning(f'Group %{group} was not captured.')
			continue
		
		# replaces all timestamps in the span with a single timestamp
		count = sub.count(' ')
		start = text[:match.start(group)].count(' ') - diff
		end = start + count
		
		timestamps[start:end] = [Timestamp(
			f'%{group}',
			timestamps[start].start,
			timestamps[end - 1].end
		)]
		diff += count - 1  # the difference in word count
	
	return True


def _write(i: int, timestamps: List[Timestamp]) -> None:
	"""
	Writes clips from a YIAY video using a list of timestamps.
	
	:param i: the video's index
	:param timestamps: the timestamps list
	"""
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
		for _, _, names in os.walk(CLIPS_PATH):
			for name in names:
				os.remove(name)
		
		for name in os.listdir(JSON_PATH):
			with open(name, 'r+') as file:
				data = json.load(file)
				file.seek(0)
				file.truncate()
				json.dump({**data, 'parsed': False}, file)

