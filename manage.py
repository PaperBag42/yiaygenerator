#!/usr/bin/env python
"""
Django manage script with an extra command to setup the video clips.
"""

from yiaygenerator import clips

import os
from sys import argv


if __name__ == '__main__':
	os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'yiaygenerator.settings')
	try:
		from django.core.management import execute_from_command_line
	except ImportError as exc:
		raise ImportError(
			"Couldn't import Django. Are you sure it's installed and "
			"available on your PYTHONPATH environment variable? Did you "
			"forget to activate a virtual environment?"
		) from exc
	
	if 'setup' in argv:
		if '--model' in argv:
			clips.model_setup()
		
		clips.make_all()
	
	else:
		execute_from_command_line(argv)
