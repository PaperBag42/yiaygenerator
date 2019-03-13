"""Generates the final video from answers and existing clips."""

from . import twitter
from .. import clips, homophones

import moviepy.video as mpy
import moviepy.video.VideoClip
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.video.compositing.CompositeVideoClip import CompositeVideoClip
from moviepy.video.compositing.concatenate import concatenate_videoclips

from tempfile import NamedTemporaryFile
from contextlib import ExitStack
import copy
import random


def yiay(question: str, hashtag: str, duration: float) -> NamedTemporaryFile:
	"""
	Generates a YIAY video.
	
	:param question: the YIAY question
	:param hashtag: the twitter hashtag the question should be answered with
	:param duration: the maximum duration of the video
	:return: a temporary file containing the generated video
	"""
	clip_list = clips.get_list()
	
	with _ClipStack(clip_list) as s:
		s.add_word('%INTRO')
		_build_question_clip(question, s)
		s.add_word('%START')
		
		s.add_word(homophones.get('and'))
		s.add_word(homophones.get('finally'))
		
		s.add_clip(VideoFileClip(str(sorted(clip_list['%OUTRO'])[-1])))  # only use the latest outro
		s.add_word('%END')
		
		tweets = twitter.tweets(hashtag, clip_list)
		_build_answer_clip(*next(tweets), s, 5)
		
		for tweet in tweets:
			_build_answer_clip(*tweet, s, 3)
			if s.duration >= duration:
				break
		
		final = NamedTemporaryFile(suffix='.mp4')
		concatenate_videoclips(s.clips).write_videofile(final.name, logger=None)
	
	return final


class _ClipStack(ExitStack):
	"""Helper class that manages clip and image files."""
	def __init__(self, clip_list: clips.ClipList) -> None:
		super().__init__()
		
		self.clips = []
		self.duration = 0.0
		
		self._original = clip_list
		self._clips = copy.deepcopy(clip_list)
	
	def add_clip(self, clip: mpy.VideoClip.VideoClip) -> None:
		"""Adds a clip object to the stack."""
		self.duration += clip.duration
		self.clips.append(self.enter_context(clip))
	
	def make_word(self, word: str) -> VideoFileClip:
		"""Gets a clip object of Jack saying a word."""
		if not self._clips[word]:
			self._clips[word] = self._original[word].copy()
		
		path = random.sample(self._clips[word], 1)[0]
		self._clips[word].remove(path)
		
		return self.enter_context(VideoFileClip(str(path)))
	
	def add_word(self, word: str) -> None:
		"""Adds a clip of Jack saying a word to the stack."""
		clip = self.make_word(word)
		self.duration += clip.duration
		self.clips.append(clip)  # already in context


def _build_question_clip(question: str, s: _ClipStack) -> None:
	"""
	Builds a clip of Jack reading the YIAY question.
	
	:param question: the question to read
	:param s: the stack to push the clips into
	"""
	reading_clip = s.enter_context(concatenate_videoclips([
		s.make_word(homophones.get(word)) for word in question.split()
	]))
	
	s.add_clip(CompositeVideoClip([
		reading_clip,
		mpy.VideoClip.TextClip(  # TODO: it doesn't look exactly like jack's font
			question,
			color='white', font='Cooper-Black', fontsize=64,
			stroke_color='black', stroke_width=3,
		).set_duration(reading_clip.duration).set_position(('center', 'bottom'))
	]))


def _build_answer_clip(answer: str, image: NamedTemporaryFile, s: _ClipStack, index: int) -> None:
	"""
	Builds a clip of Jack reading a YIAY answer,
	and adds it to the stack.
	
	:param answer: the answer as text to read
	:param image: image of a tweet to display
	:param s: the stack to push the clips into
	:param index: the index to insert the clip at in the stack
	"""
	reading_clip = s.enter_context(concatenate_videoclips([
		s.make_word(homophones.get(word)) for word in answer
	]))
	clip = s.enter_context(CompositeVideoClip([
		reading_clip,
		mpy.VideoClip.ImageClip(s.enter_context(image).name, duration=reading_clip.duration)
			.set_position(('center', 'bottom')),
	]))
	
	s.duration += clip.duration
	s.clips.insert(index, clip)
