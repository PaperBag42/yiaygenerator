"""
Provides a list of homophones to let the same video clips be used as different words,
thus allowing broader usage of the video clips.
"""

import re

HOMOPHONES_PATH = 'expr/assets/homophone_list.csv'

_non_letter = re.compile(r'[^a-z]')

_homophones = {}  # words that sound like other words

# parses homophone_list.csv
with open(HOMOPHONES_PATH) as file:
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
			_homophones[word] = homophone


def get_homophone(word: str) -> str:
	"""
	Searches for a homophone of a given word.

	:param word: the word to find a homophone of
	:return:
		The first homophone found for the the word,
		or the given word if no homophone was found.
	"""
	word = _non_letter.sub('', word.lower())
	return _homophones.get(word, word)

