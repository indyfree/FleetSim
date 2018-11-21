# flake8: noqa
import logging
logger = logging.getLogger('vppsim.data')

from .loader import load_car2go
from .process import process_car2go
