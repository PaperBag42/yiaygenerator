"""Generates video clips using the speech-to-text results."""

from typing import List, Iterable

from .. import homophones
from . import youtube, stt
from .stt import Timestamp, json_path
from ._logging import logger

import moviepy.video as mpy
import moviepy.video.VideoClip
import moviepy.video.compositing.CompositeVideoClip
import moviepy.video.io.VideoFileClip
import moviepy.video.io.downloader
import moviepy.video.tools.drawing
import moviepy.video.fx.resize

import re
import json
from pathlib import Path
from collections import Counter

clips_path = Path('expr/clips/')
avatar_path = Path('expr/avatar.jpeg')

AVATAR_URL = 'https://avatars0.githubusercontent.com/u/39616775?v=4'
END_CARD_START = 379
CLIP_SIZE = 1280, 720
BOX_SIZE = 412, 231
TEXT_POS = 828, 361
AVATAR_POS = 828, 101


# end card overlay setup (avatar and link at the end)

mpy.io.downloader.download_webfile(AVATAR_URL, avatar_path)
avatar = mpy.VideoClip.ImageClip(str(avatar_path)) \
	.fx(mpy.fx.resize.resize, height=BOX_SIZE[1])
center = avatar.w / 2, avatar.h / 2

_end_card = mpy.compositing.CompositeVideoClip.CompositeVideoClip([
	avatar
		.set_position((int(AVATAR_POS[0] + BOX_SIZE[0] / 2 - center[0]), AVATAR_POS[1]))
		.set_mask(mpy.VideoClip.ImageClip(mpy.tools.drawing.circle(
			avatar.size, center, min(center),
		), ismask=True)),
	mpy.VideoClip.TextClip(
		'www.github.com/\nPaperBag42/yiaygenerator',
		font='Cooper-Black', size=BOX_SIZE,
	).set_position(TEXT_POS),
], size=CLIP_SIZE)

del avatar, center


def make_all() -> None:
	"""
	Makes video clips from all YIAY videos.
	"""
	i = 1
	while True:
		try:
			make_from(i)
		except youtube.DownloadError:
			pass
		except IndexError:
			break
		
		i += 1


def make_from(i: int) -> None:
	"""
	Makes video clips from a single YIAY video.
	
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
	# TODO: make a cool end card
	# r'(?P<END>.*? episode )'
	r'(?P<END>.* )'
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
	word_count = Counter()
	
	with youtube.video(i, only_audio=False) as video:
		with mpy.io.VideoFileClip.VideoFileClip(str(video)) as clip:
			
			logger.info(f'Writing {len(timestamps)} clips...')
			for word, start, end in timestamps:
				
				dirname = clips_path / (word if word.startswith("%") else homophones.get(word))
				if not dirname.exists():
					dirname.mkdir()
				
				clip.subclip(start, end).write_videofile(
					str(dirname / f'{i:03d}-{count[word]:03d}.mp4'),
					verbose=False, progress_bar=False
				)
				word_count[word] += 1
		
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
	Deletes the clips and resets the 'clipped' attribute in the JSON files.
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