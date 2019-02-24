"""Template filters for imitating Twitter statuses."""

import django.template
import django.utils.timezone
from datetime import datetime, timedelta

register = django.template.Library()


@register.filter(is_safe=True)
def count(num: int) -> str:
	"""
	Format for action counts on Twitter.
	:param num: number of replies/retweets/favorites on a tweet
	:return: the number, along with 'K' for thousands and 'M' for millions
	"""
	if num < 1_000:
		return str(num)  # 1 21 321
	if num < 1_000_000:
		return f'{num / 1_000:.{1 if num < 10_000 else 0}f}K'  # 4.3K 54K 654K
	return f'{num / 1_000_000:.{1 if num < 10_000_000 else 0}f}M'  # 7.6M 87M 987M


@register.filter(is_safe=True)
def age(created_at: str) -> str:
	"""
	Format for the date in which a tweet was created
	:param created_at: string representation of a date
	:return:
		- only hours if the tweet is from today
		- date and month if the tweet is from this year
	"""
	time = datetime.strptime(created_at, '%a %b %d %H:%M:%S %z %Y')
	passed = django.utils.timezone.now() - time
	
	if passed < timedelta(1):
		return f'{passed.seconds // 3_600}h'
	if passed < timedelta(365):
		return f'{time:%b %d}'
	return f'{time:%d %b %Y}'
