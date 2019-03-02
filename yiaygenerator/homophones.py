"""
Provides a list of homophones (words that sound like other words)
to let the same video clips be used as different words,
thus allowing broader usage of the video clips.
"""

from typing import Dict

import re

HOMOPHONES_PATH = 'externals/homophone_list.csv'

invalid = re.compile(r'[^a-z]')


def _load() -> Dict[str, str]:
	"""
	Loads the homophones list from a CSV file
	I stole from homophone.com.
	"""
	with open(HOMOPHONES_PATH) as file:
		homophones = {}
		i = -1
		homophone = ''
		
		next(file)
		for line in file:
			_, _, word, ind = line.split(',')
			word = invalid.sub('', word.lower())
			ind = int(ind)
			
			if i != ind:
				i = ind
				homophone = word
			else:
				homophones[word] = homophone
	
		return homophones


_homophones = _load()


def get(word: str) -> str:
	"""
	Searches for a homophone of a given word.

	:param word: the word to find a homophone of
	:return:
		The first homophone found for the the word,
		or the given word if no homophone was found.
	"""
	word = invalid.sub('', word.lower())
	return _homophones.get(word, word)
