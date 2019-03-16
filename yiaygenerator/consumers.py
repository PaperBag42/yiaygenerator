"""Django Channels consumer(s) for Websocket communication."""

from channels.generic.websocket import WebsocketConsumer

import urllib.parse
import time


class YiayConsumer(WebsocketConsumer):
	"""
	Websocket consumer that manages the YIAY generation.
	Sends progress updates in real-time,
	and sends the video file when the generation is done.
	"""
	
	def connect(self):
		"""
		Connects to a client and initiates YIAY generation.
		
		**Protocol Specification:**
		Progress: P<byte>
		Data:     D<bytes>
		"""
		self.accept()
		query = urllib.parse.parse_qs(self.scope['query_string'].decode())
		dummy_func(f'question = {query["question"][0]}, hashtag = {query["hashtag"][0]}', self)
	

def dummy_func(text: str, consumer: WebsocketConsumer):
	for i in range(100):
		consumer.send(text)
		time.sleep(3)

