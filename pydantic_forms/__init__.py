import logging
import os

__version__ = "0.1.0"
__package____ = "pyschemaforms"
__description__ = "A package for creating and validating JSON schemas."
__author__ = "Mike Ryan"
__name__ = "pyschemaforms"


STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

# Set up package-level logger
logger = logging.getLogger(__package____)
if not logger.hasHandlers():
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s %(name)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
logger.setLevel(logging.DEBUG)
logger.propagate = False  # <--- Add this line to prevent duplicate logs
