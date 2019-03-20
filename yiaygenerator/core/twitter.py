"""
Collects twitter posts to use as YIAY answers.

What it does:
	- Searches for tweets containing a hashtag with the Twitter API
	- Converts tweets to words with existing associated video clips
	- Renders tweets to HTML and then to images using WKHtmlToPdf
"""

from typing import Container, Generator, Tuple, Dict, Optional, List

from .. import homophones

import twitter
import django.template.loader
from django.utils import safestring
import imgkit

from os import environ
from tempfile import NamedTemporaryFile
import logging

logger = logging.getLogger(__name__)


def tweets(hashtag: str, dictionary: Container[str]) -> Generator[Tuple[List[str], NamedTemporaryFile], None, None]:
	"""
	Gets and processes Twitter posts to be used as YIAY answers.
	
	:param hashtag: a Twitter hashtag to find tweets by
	:param dictionary: words that Jack will be able to say
	:return: Pairs of tweet images and words to read
	"""
	if not hashtag.startswith('#'):
		hashtag = f'#{hashtag}'
	
	search = twitter.Twitter(
		auth=twitter.OAuth2(bearer_token=environ['TWITTER_TOKEN']),
		retry=True,
	).search.tweets
	
	max_id = None
	while True:
		res = search(
			q=hashtag, max_id=max_id,
			lang='en',
			tweet_mode='extended',
		)
		# tweet_mode='extended' should disable truncating
		# but I think I saw tweets get truncated still?
		logger.info(f'Loading {len(res["statuses"])} tweets with {hashtag}...')
		
		for tweet in res['statuses']:
			tweet = tweet.get('retweeted_status', tweet)  # if the tweet is a retweet, switch to original
			readable = _get_readable_text(tweet, dictionary)
			if readable is not None:
				logger.debug(f'Using tweet {tweet["id_str"]}')
				yield readable, _image(tweet)
		
		next_res = res['search_metadata'].get('next_results')
		if next_res is None:
			break
		max_id = next_res[8:26]  # '?max_id={max_id}&q=...'


def _get_readable_text(tweet: Dict, dictionary: Container[str]) -> Optional[List[str]]:
	"""
	HARD PART #2
	Converts a tweet's content to text Jack can read.
	
	:param tweet: a tweet object from the Twitter API
	:param dictionary: words that Jack will be able to say
	:return: words for Jack to read, or None if the tweet is not readable
	"""
	start, end = tweet['display_text_range']
	chars = list(tweet['full_text'][start:end])
	diff = start
	
	# remove all entities?
	for entity in sum(tweet['entities'].values(), []):
		e_start, e_end = entity['indices']
		
		if e_start >= start and e_end <= end:
			del chars[e_start - diff:e_end - diff]
			diff += e_end - e_start
	
	# TODO: handle unicode characters (gonna be very hard)
	# some ideas:
	# convert numbers to names
	# convert russian letters and such to letters that look the same
	# detect camelCase / PascalCase
	
	words = ''.join(chars).lower().split()
	for i, word in enumerate(words):
		new = homophones.get(word)
		if new in dictionary:
			words[i] = new
			continue
		
		# try to split to letters
		# letters = [homophones.get(c) for c in word if not homophones.invalid.match(c)]
		# if all(letter in dictionary for letter in letters):
		# 	words[i:i + 1] = letters
		# 	continue
		
		logger.debug(f'Failed to convert tweet {tweet["id_str"]} to readable text.')
		return  # failed :(
	
	return words


_template = django.template.loader.get_template('yiaygenerator/_tweet.html')
_OFFSET = 520
_options = {
	'log-level': 'error',
	'selector': '#main',
	'quality': 100,
	'height': 720,
	# FIXME
	# I've been killing bugs from this shit for a week,
	# and now it decided to move 520px to the left for some reason
	# so I'll just move it to the right
	'crop-x': _OFFSET,
	'crop-w': _OFFSET,
}


def _image(tweet: Dict) -> NamedTemporaryFile:
	"""
	Converts data from a tweet to an image of the tweet.
	
	:param tweet: a tweet object from the Twitter API
	:return: path to the tweet image file.
	"""
	file = NamedTemporaryFile(suffix='.jpg')
	
	imgkit.from_string(_template.render({
		**tweet,
		'full_text': _get_display_text(tweet),
	}), file.name, _options)
	
	return file


def _get_display_text(tweet: Dict) -> safestring.SafeText:
	"""
	Converts a tweet's content to HTML for displaying.
	
	:param tweet: a tweet object from the Twitter API
	:return: an HTML representation of the tweet's text
	"""
	start, end = tweet['display_text_range']
	chars = list(tweet['full_text'][start:end])
	diff = start
	
	# make entities blue
	for entity in sum(tweet['entities'].values(), []):
		# extended_entities always included in entities?
		e_start, e_end = entity['indices']
		
		if e_start >= start and e_end <= end:
			chars.insert(e_end - diff, '</b></a>')
			chars.insert(e_start - diff, '<a class="pretty-link" dir="ltr"><b>')
			diff -= 2
	
	# note: the Twitter API automatically HTML-escapes the content
	# I'll be in trouble if it decides to stop doing that
	return safestring.mark_safe(''.join(chars))


def get_token() -> str:
	"""
	Returns a bearer token to be cached and used
	to authenticate Twitter API requests.
	"""
	return twitter.oauth2_dance(environ['TWITTER_KEY'], environ['TWITTER_SECRET'])
