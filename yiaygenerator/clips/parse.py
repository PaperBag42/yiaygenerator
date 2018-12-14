from typing import List, Iterable

from . import youtube, stt
from ._logging import logger

import re

CLIPS_PATH = 'expr/clips/'
LOG_PATH = 'expr/log.csv'

WORD, START, END = 0, 1, 2


def generate(i: int) -> None:
	"""
	Generates clips from a new YIAY video.
	
	:param i: the video's index in the playlist
	"""
	pass


_pattern = re.compile(
	r'(?P<INTRO>.*?asked you )?'  # ok
	r'(?P<QUESTION>.*?)'  # ok
	r'(?P<START>(here .*?)?answers )?'  # will probably break a lot (he sometimes says "let's go" or other random stuff)
	r'(?P<CONTENT>.*)'  # ok
	# TODO: sponsor
	r'(?P<OUTRO>(leave|let) .*?YIAY )'  # ok?
	r'(?P<END>.*)'  # ok
)


def parse(text: str, timestamps: List[List]):
	match = _pattern.match(text)


def test(inds: Iterable[int]) -> None:
	"""
	Tests the RegEx pattern against a range of YIAY videos.
	
	:param inds: indexes of videos to test
	"""
	matched = 0
	total = 0
	for i in inds:
		logger.ind = i
		total += 1
		
		text = stt.speech_to_text(i)[0]
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
