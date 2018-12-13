from __future__ import annotations
from typing import Dict

import logging


class _IndexAdapter(logging.LoggerAdapter):
	ind: int
	
	def process(self: _IndexAdapter, msg: str, kwargs: Dict):
		return f'YIAY#{self.ind:03d}:{msg}', kwargs


logger = _IndexAdapter(logging.getLogger('yiaygenerator.clips'), {})
