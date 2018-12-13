from typing import Dict

import logging


class IndexAdapter(logging.LoggerAdapter):
	i: int
	
	def process(self, msg: str, kwargs: Dict):
		return f'YIAY#{self.i:03d}:{msg}', kwargs


logger = IndexAdapter(logging.getLogger('yiaygenerator.clips'), {})
