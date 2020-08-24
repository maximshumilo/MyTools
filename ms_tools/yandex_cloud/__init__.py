import logging

from .object_storage import ObjectStorage

date_format = '%Y-%m-%d %H:%M:%S'
log_format = '[%(asctime)s %(levelname)s] %(message)s'
logging.basicConfig(level=logging.INFO, format=log_format, datefmt=date_format)
logger = logging.getLogger(__name__)
