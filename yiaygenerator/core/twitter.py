"""Collects twitter posts to use as YIAY answers."""

from typing import Generator, Dict

import twitter
import django.template.loader
import imgkit
from django.utils import safestring

import contextlib
import tempfile
import pathlib
from os import environ, PathLike


def tweets(hashtag: str) -> Generator[PathLike, None, None]:
	"""
	Gets and processes Twitter posts to be used as YIAY answers.
	:param hashtag: a Twitter hashtag to find tweets by
	:return:
	"""
	if not hashtag.startswith('#'):
		hashtag = f'#{hashtag}'
	
	search = twitter.Twitter(
		auth=twitter.OAuth2(bearer_token=environ['TWITTER_TOKEN']),
		retry=True,
	).search.tweets
	
	with contextlib.ExitStack() as images:
		max_id = None
		while True:
			res = search(
				q=hashtag, max_id=max_id,
				lang='en',
				tweet_mode='extended',
				include_entities=True,  # default despite documentation saying otherwise?
			)
			# tweet_mode='extended' should disable truncating
			# but I think I saw tweets get truncated still?
			
			yield from (images.enter_context(_image(tweet)) for tweet in res['statuses'])
			
			if 'next_results' not in res['search_metadata']:
				break
			max_id = min(s['id'] for s in res['statuses'])


def _validate(tweet: Dict):
	pass


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


@contextlib.contextmanager
def _image(tweet: Dict) -> Generator[PathLike, None, None]:
	"""
	Converts data from a tweet to an image of the tweet.
	:param tweet: a tweet object from the Twitter API
	:return: path to the tweet image file.
	"""
	with tempfile.NamedTemporaryFile(suffix='.jpg') as file:
		name = file.name
		imgkit.from_string(_template.render({
			**tweet,
			'full_text': _get_display_text(tweet),
		}), name, _options)
		
		yield pathlib.Path(name)


def _get_display_text(tweet: Dict) -> safestring.SafeText:
	"""
	Transforms a tweet's content to HTML for displaying.
	:param tweet: a tweet object from the Twitter API
	:return: an HTML representation of the tweet's text
	"""
	start, end = tweet['display_text_range']
	text = list(tweet['full_text'][start:end])
	diff = start
	
	# make entities blue
	for entity in sum(tweet['entities'].values(), []):
		# extended_entities always included in entities?
		e_start, e_end = entity['indices']
		
		if e_start >= start and e_end <= end:
			text.insert(e_end - diff, '</b></a>')
			text.insert(e_start - diff, '<a class="pretty-link" dir="ltr"><b>')
			diff -= 2
	
	# note: the Twitter API automatically HTML-escapes the content
	# I'll be in trouble if it decides to stop doing that
	return safestring.mark_safe(''.join(text))


def get_token() -> str:
	"""
	Returns a bearer token to be cached and used
	to authenticate Twitter API requests.
	"""
	return twitter.oauth2_dance(environ['TWITTER_KEY'], environ['TWITTER_SECRET'])
