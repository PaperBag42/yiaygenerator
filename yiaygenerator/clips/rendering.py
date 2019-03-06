"""
Generates video clips using the speech-to-text results.

What it does:
	- Puts the video's transcript through a RegEx pattern,
	  in order to capture the common phases of a YIAY video
	  (intro, outro, etc.)
	- Adds my avatar and a URL to the video's end card
	- Writes each word or part to a separate video file
"""

from typing import NewType, Optional, Dict, Set, Sequence, Iterable

from .. import homophones
from . import youtube, stt
from .stt import Timestamp, json_path
from ._logging import logger

import moviepy.video as mpy
import moviepy.video.VideoClip
import moviepy.video.io.VideoFileClip
import moviepy.video.tools.drawing
import moviepy.video.fx.resize
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip

from django.core.cache import cache

import re
import json
from os import PathLike
from pathlib import Path
from collections import Counter

clips_path = Path('expr/clips/')


def make_all() -> None:
	"""Makes video clips from all YIAY videos."""
	with _end_card_overlay() as end_card:
		
		i = 1
		while True:
			try:
				make_from(i, end_card)
			except youtube.DownloadError:
				pass
			except IndexError:
				break
			i += 1
	
	cache.set('clips', {p.name: set(p.iterdir()) for p in clips_path.iterdir()})


def make_from(i: int, end_card: Optional[CompositeVideoClip] = None) -> None:
	"""
	Makes video clips from a single YIAY video.
	
	:param i: the video's index in the playlist
	:param end_card: an overlay clip to apply on end cards.
	"""
	logger.ind = i
	clipped, text, timestamps = stt.speech_to_text(i)
	
	if not clipped and _group(text, timestamps):  # don't use videos that don't match
		_write(i, timestamps, end_card)


ClipList = NewType('ClipList', Dict[str, Set[PathLike]])


def get_list() -> ClipList:
	"""
	Returns a dict mapping words to paths
	to the available clips.
	"""
	return cache.get_or_set(
		'clips', lambda: {p.name: set(p.iterdir()) for p in clips_path.iterdir()}
	)


# HARD PART #1
_pattern = re.compile(
	r'(?P<INTRO>.*? asked you )?'
	r'.*? '
	r'(?P<START>(here .*? )?answers )?'  # breaks a lot (he sometimes says "let's go" or other random stuff)
	r'.* '
	# TODO: sponsor
	r'(?P<OUTRO>(leave|let) .*? YIAY )'
	# r'(?P<END>.*? episode )'  # TODO: add the user's previous clip?
	r'(?P<END>.* )'
)


def _group(text: str, timestamps: Sequence[Timestamp]) -> bool:
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


def _write(i: int, timestamps: Sequence[Timestamp], end_card: Optional[CompositeVideoClip]) -> None:
	"""
	Writes clips from a YIAY video using a list of timestamps.
	
	:param i: the video's index
	:param timestamps: the timestamps list
	:param end_card: an overlay clip to apply on end cards.
	"""
	word_count = Counter()
	success = True
	
	with youtube.video(i, only_audio=False) as video:
		with mpy.io.VideoFileClip.VideoFileClip(str(video)) as clip:
			
			logger.info(f'Writing {len(timestamps)} clips...')
			for word, start, end in timestamps:
				logger.debug(f'{word}: {start:.2f} - {end:.2f}')
				
				dirname = clips_path / (word if word.startswith("%") else homophones.get(word))
				if not dirname.exists():
					dirname.mkdir()
				
				sub = clip.subclip(start, end)
				if word == '%END' and i >= END_CARD_START and end_card is not None:
					logger.info('Applying overlay to end card.')
					sub = mpy.compositing.CompositeVideoClip.CompositeVideoClip([
						sub, end_card.set_duration(sub.duration)
					])
				
				try:
					sub.write_videofile(str(dirname / f'{i:03d}-{word_count[word]:03d}.mp4'), logger=None)
				except IOError:
					logger.warning(f'Failed at {start:.2f}-{end:.2f}')
					success = False
				
				word_count[word] += 1
	
	if success:
		_set_clipped(json_path / f'{i:03d}.json', True)
	

def _set_clipped(path: PathLike, clipped: bool) -> None:
	"""Updates a JSON file to indicate whether the video was successfully clipped."""
	with open(path, 'r+') as file:
		data = json.load(file)
		file.seek(0)
		file.truncate()
		json.dump({**data, 'clipped': clipped}, file, separators=(',', ':'))


AVATAR_URL = 'https://avatars0.githubusercontent.com/u/39616775?v=4'
END_CARD_START = 379
CLIP_SIZE = 1280, 720
BOX_SIZE = 412, 231
TEXT_POS = 828, 361
AVATAR_POS = 828, 101


def _end_card_overlay() -> CompositeVideoClip:
	"""
	Builds an overlay clip to apply on end cards.
	Currently contains:
		- My Github avatar
		- The Github repo URL
	
	:return: the clip object to use as overlay
	"""
	avatar = mpy.VideoClip.ImageClip(AVATAR_URL) \
		.fx(mpy.fx.resize.resize, height=BOX_SIZE[1])
	center = avatar.w / 2, avatar.h / 2
	
	return CompositeVideoClip([
		avatar
			.set_position((AVATAR_POS[0] + BOX_SIZE[0] // 2 - center[0], AVATAR_POS[1]))  # put it in the top right box
			.set_mask(mpy.VideoClip.ImageClip(mpy.tools.drawing.circle(  # make it circle shaped
				avatar.size, center, min(center),
			), ismask=True)),
		mpy.VideoClip.TextClip(
			'www.github.com/\nPaperBag42/yiaygenerator',
			font='Cooper-Black', size=BOX_SIZE,
		).set_position(TEXT_POS),
	], size=CLIP_SIZE)


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


def reset() -> None:
	"""Deletes the clips and resets the 'clipped' attribute in the JSON files."""
	if input('ARE YOU SURE ABOUT THAT [Y/N]') != 'N':  # just making sure
		for word in clips_path.iterdir():
			for clip in word.iterdir():
				clip.unlink()
		
		for path in json_path.iterdir():
			_set_clipped(path, False)
