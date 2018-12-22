"""
Generates clips from existing YIAY videos
to be used as material for the YIAY generator.

What it does:
	- Downloads the video from Youtube
	- Sends the audio to IBM's Watson Developer Cloud API
	- Puts the results through a RegEx pattern to detect the important parts
	- splits the video to clips and writes them to files
"""

from .parser import create, CLIPS_PATH
