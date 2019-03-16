"""
HARD PART #1
Work with Regular Expressions to parse YIAY videos.

Puts the video's transcript through a RegEx pattern,
in order to capture the common phases of a YIAY video
(intro, outro, etc.)
"""

from typing import Sequence, Iterable

from . import stt
from .stt import Timestamp
from ._logging import logger

import re
import collections

# Turns out there's a limit to what a single RegEx can do (who knew?).
# So I'll be using a bunch of different patterns as fallback to each other.
# Good idea right?
patterns = [
	re.compile(
		r'(?P<INTRO>.*? asked you )?'
		r'.*? '
		r'(?P<START>here .{,50}?answers )'  # breaks a lot (he sometimes says "let's go" or other random stuff)
		r'.* '
		# TODO: sponsor
		r'(?P<OUTRO>(leave|let) .*? YIAY )'
		# r'(?P<END>.*? episode )'  # TODO: add the user's previous clip?
		r'(?P<END>.*)'
	),
	re.compile(
		r'(?P<INTRO>.*? asked you )?'
		r'.* '
		r'(?P<OUTRO>(leave|let) .*? YIAY )'
		r'(?P<END>.*)'
	),
]


def parse(text: str, timestamps: Sequence[Timestamp]) -> bool:
	"""
	Tries to detect parts of the video that are typical	for a YIAY video.
	Groups the detected parts into single clips in the timestamp list.

	:param text: the video's full transcript to be matched against a RegEx pattern
	:param timestamps: the timestamps list to be modified
	:return: true if the match succeeded
	"""
	for pattern in patterns:
		match = pattern.fullmatch(text)
		if match is not None:
			break
	else:
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


def test(inds: Iterable[int]) -> None:
	"""
	Tests the RegEx pattern against a range of YIAY videos.

	:param inds: indexes of videos to test
	"""
	groups = collections.Counter()
	matched = 0
	total = 0
	for i in inds:
		logger.ind = i
		total += 1
		
		text = stt.speech_to_text(i)[1]
		
		for pattern in patterns:
			match = pattern.fullmatch(text)
			if match is not None:
				break
		else:
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
