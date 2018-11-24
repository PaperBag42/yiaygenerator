from typing import List

import youtube

import logging  # TODO: call basicConfig() on initialization

import re
import collections

CLIPS_PATH = 'expr/clips/'
LOG_PATH = 'expr/log.csv'

WORD, START, END = 0, 1, 2


def generate(i: int) -> None:
	"""
	Generates clips from a new YIAY video.
	:param i: the video's index in the playlist
	"""
	pass


pattern = re.compile(
	r'(?P<intro>.*?asked you )?'  # ok
	r'(?P<question>.*?)'  # ok
	r'(?P<start>(here .*?)?answers )?'  # will probably break a lot (he sometimes says "let's go" or other random stuff)
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
