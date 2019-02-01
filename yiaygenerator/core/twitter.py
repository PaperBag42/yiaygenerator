"""
Collects twitter posts to use as YIAY answers.
"""
from typing import Generator, Dict, List

import twitter

from os import environ


def tweets(hashtag: str) -> Generator[None]:
	"""
	Gets and processes Twitter posts to be used as YIAY answers.
	:param hashtag: a Twitter hashtag to find tweets by
	:return:
	"""
	if not hashtag.startswith('#'):
		hashtag = f'#{hashtag}'
	
	client = twitter.Twitter(
		auth=twitter.OAuth2(bearer_token=environ['TWITTER_TOKEN']),
		retry=True,
	)
	
	max_id = None
	while True:
		res = client.search.tweets(
			q=hashtag, max_id=max_id,
			lang='en',
			tweet_mode='extended',
			include_entities=True,
		)
		
		yield None
		
		if 'next_results' not in res['search_metadata']:
			break
		max_id = min(s['id'] for s in res['statuses'])


def _validate(tweet: Dict):
	pass


def _processed(data: List[Dict]):
	pass


def get_token() -> str:
	"""
	Returns a bearer token to be cached and used
	to authenticate Twitter API requests.
	"""
	return twitter.oauth2_dance(environ['TWITTER_KEY'], environ['TWITTER_SECRET'])
