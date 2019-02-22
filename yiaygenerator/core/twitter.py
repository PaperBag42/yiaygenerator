"""
Collects twitter posts to use as YIAY answers.
"""
from typing import Generator, Dict, List, ContextManager

import twitter
import django.template.loader
import imgkit

import contextlib
import tempfile
import pathlib
from os import environ, PathLike


def tweets(hashtag: str) -> Generator[PathLike]:
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
				include_entities=True,
			)
			
			yield from (images.enter_context(_image(tweet)) for tweet in res['statuses'])
			
			if 'next_results' not in res['search_metadata']:
				break
			max_id = min(s['id'] for s in res['statuses'])


def _validate(tweet: Dict):
	pass


_template = django.template.loader.get_template('yiaygenerator/_tweet.html')
_OFFSET = 520
_options = {
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
def _image(data: List[Dict]) -> ContextManager[PathLike]:
	"""
	Converts data from a tweet to an image of the tweet.
	:param data: a tweet object from the Twitter API.
	:return: path to the tweet image file.
	"""
	with tempfile.NamedTemporaryFile(suffix='.jpg') as file:
		name = file.name
		imgkit.from_string(_template.render(data), name)
		
		yield pathlib.Path(name)


def get_token() -> str:
	"""
	Returns a bearer token to be cached and used
	to authenticate Twitter API requests.
	"""
	return twitter.oauth2_dance(environ['TWITTER_KEY'], environ['TWITTER_SECRET'])
