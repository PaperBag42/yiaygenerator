"""
Generates video clips using the speech-to-text results.

What it does:
	-
	- Adds my avatar and a URL to the video's end card
	- Writes each word or part to a separate video file
"""

from typing import NewType, Dict, Set, Sequence

from .. import homophones
from . import youtube, stt, parsing
from .stt import Timestamp, json_path
from ._logging import logger

import moviepy.video as mpy
import moviepy.video.VideoClip
import moviepy.video.io.VideoFileClip
import moviepy.video.tools.drawing
import moviepy.video.fx.resize
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
import youtube_dl
from django.core.cache import cache

import json
from os import PathLike
from pathlib import Path
from collections import Counter

clips_path = Path('expr/clips/')


def make_all() -> None:
	"""Makes video clips from all YIAY videos."""
	i = 1
	while True:
		try:
			make_from(i)
		except IndexError:
			break
		i += 1
	
	cache.set('clips', {p.name: set(p.iterdir()) for p in clips_path.iterdir()})


def make_from(i: int) -> None:
	"""
	Makes video clips from a single YIAY video.
	
	:param i: the video's index in the playlist
	"""
	logger.ind = i
	try:
		clipped, text, timestamps = stt.speech_to_text(i)
		
		if not clipped and parsing.parse(text, timestamps):  # don't use videos that don't match
			_write(i, timestamps)
	
	except youtube_dl.DownloadError:
		logger.error('Youtube failed to provide video')


ClipList = NewType('ClipList', Dict[str, Set[PathLike]])


def get_list() -> ClipList:
	"""
	Returns a dict mapping words to paths
	to the available clips.
	"""
	return cache.get_or_set(
		'clips', lambda: {p.name: set(p.iterdir()) for p in clips_path.iterdir()}
	)


def _write(i: int, timestamps: Sequence[Timestamp]) -> None:
	"""
	Writes clips from a YIAY video using a list of timestamps.
	
	:param i: the video's index
	:param timestamps: the timestamps list
	"""
	word_count = Counter()
	
	with youtube.video(i, only_audio=False) as video:
		with mpy.io.VideoFileClip.VideoFileClip(video.name) as clip:
			
			logger.info(f'Writing {len(timestamps)} clips...')
			for word, start, end in timestamps:
				logger.debug(f'{word}: {start:.2f} - {end:.2f}')
				
				dirname = clips_path / (word if word.startswith("%") else homophones.get(word))
				if not dirname.exists():
					dirname.mkdir()
				
				sub = clip.subclip(start, end)
				if word == '%END' and i >= END_CARD_START:
					logger.info('Applying overlay to end card.')
					sub = mpy.compositing.CompositeVideoClip.CompositeVideoClip([
						sub, _end_card.set_duration(sub.duration)
					])
				
				try:
					sub.write_videofile(str(dirname / f'{i:03d}-{word_count[word]:03d}.mp4'), logger=None)
				except IOError:
					logger.warning(f'Failed at {start:.2f}-{end:.2f}')
				
				word_count[word] += 1
	
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


def _build_end_card_overlay() -> CompositeVideoClip:
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


# no need to close this clip, it's just some imageio arrays
_end_card = _build_end_card_overlay()


def reset() -> None:
	"""Deletes the clips and resets the 'clipped' attribute in the JSON files."""
	if input('ARE YOU SURE ABOUT THAT [Y/N]') != 'N':  # just making sure
		for word in clips_path.iterdir():
			for clip in word.iterdir():
				clip.unlink()
		
		for path in json_path.iterdir():
			_set_clipped(path, False)
