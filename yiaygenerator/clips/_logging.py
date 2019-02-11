"""Module-level logging configuration."""

from typing import Dict

import logging


class _IndexAdapter(logging.LoggerAdapter):
	ind: int
	
	def process(self, msg: str, kwargs: Dict):
		return f'YIAY#{self.ind:03d}:{msg}', kwargs


logger: logging.Logger = _IndexAdapter(logging.getLogger('yiaygenerator.clips'), {})
"""A custom module-level logger that logs the index of the relevant YIAY video as well."""
