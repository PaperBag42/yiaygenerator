"""Generates video clips using the speech-to-text results."""

from typing import List, Iterable

from .. import homophones
from . import youtube, stt
from .stt import Timestamp, json_path
from ._logging import logger

import moviepy.video.io.VideoFileClip

import re
import json
import pathlib
from collections import Counter

clips_path = pathlib.Path('expr/clips/')


def create_all() -> None:
	"""
	Creates video clips from all YIAY videos.
	"""
	i = 1
	while True:
		try:
			create(i)
		except youtube.DownloadError:
			pass
		except IndexError:
			break
		
		i += 1


def create(i: int) -> None:
	"""
	Creates video clips from a single YIAY video.
	
	:param i: the video's index in the playlist
	"""
	logger.ind = i
	clipped, text, timestamps = stt.speech_to_text(i)
	
	if not clipped and _group(text, timestamps):  # don't use videos that don't match
		_write(i, timestamps)


_pattern = re.compile(
	r'(?P<INTRO>.*? asked you )?'
	r'.*? '
	r'(?P<START>(here .*? )?answers )?'  # will probably break a lot (he sometimes says "let's go" or other random stuff)
	r'.* '
	# TODO: sponsor
	r'(?P<OUTRO>(leave|let) .*? YIAY )'
	# r'(?P<END>.*? episode )'
	# TODO: make a cool end card
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
	count = Counter()
	
	with youtube.video(i, only_audio=False) as video:
		with moviepy.video.io.VideoFileClip.VideoFileClip(video) as clip:
			
			logger.info(f'Writing {len(timestamps)} clips...')
			for word, start, end in timestamps:
				
				dirname = clips_path / (word if word.startswith("%") else homophones.get(word))
				if not dirname.exists():
					dirname.mkdir()
				
				clip.subclip(start, end).write_videofile(
					str(dirname / f'{i:03d}-{count[word]:03d}.mp4'),
					verbose=False, progress_bar=False
				)
				count[word] += 1
		
	with open(json_path / f'{i:03d}.json', 'r+') as file:
		data = json.load(file)
		file.seek(0)
		file.truncate()
		json.dump({**data, 'clipped': True}, file, separators=(',', ':'))


def test(inds: Iterable[int]) -> None:
	"""
	Tests the RegEx pattern against a range of YIAY videos.
	
	:param inds: indexes of videos to test
	"""
	groups = Counter()
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
			if not part:
				logger.warning(f'Group %{name} was not captured.')
				continue
			groups[name] += 1
			logger.info(f'Group %{name}: {100 * len(part) / len(text):.2f}% of video.')
			
	print(f'Matched {matched}/{total} ({100 * matched / total:.2f}%) videos.')
	for name, count in groups.items():
		print(f'Group %{name}: {count}/{matched} ({100 * count / matched:.2f}%) videos.')


def reset():
	"""
	Deletes the clips and resets the 'parsed' attribute in the JSON files.
	"""
	if input('ARE YOU SURE ABOUT THAT [Y/N]') != 'N':  # just making sure
		for word in clips_path.iterdir():
			for clip in word.iterdir():
				clip.unlink()
		
		for name in json_path.iterdir():
			with open(name, 'r+') as file:
				data = json.load(file)
				file.seek(0)
				file.truncate()
				json.dump({**data, 'clipped': False}, file, separators=(',', ':'))
