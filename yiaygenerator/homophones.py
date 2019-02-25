"""
Provides a list of homophones (words that sound like other words)
to let the same video clips be used as different words,
thus allowing broader usage of the video clips.
"""

from django.core.cache import cache

import re

HOMOPHONES_PATH = 'externals/homophone_list.csv'

_non_letter = re.compile(r'[^a-z]')


def load() -> None:
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
			word = _non_letter.sub('', word.lower())
			ind = int(ind)
			
			if i != ind:
				i = ind
				homophone = word
			else:
				homophones[word] = homophone
	
	cache.set('homophones', homophones)


# TODO: check if it really needs to be cached
# if not, revert 77f7f719


def get(word: str) -> str:
	"""
	Searches for a homophone of a given word.

	:param word: the word to find a homophone of
	:return:
		The first homophone found for the the word,
		or the given word if no homophone was found.
	"""
	word = _non_letter.sub('', word.lower())
	return cache.get('homophones').get(word, word)
