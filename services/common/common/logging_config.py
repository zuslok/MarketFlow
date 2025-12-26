import logging
import sys
from .config import settings

def setup_logging(service_name: str) -> logging.Logger:
    """ Create logger for service"""
    logger = logging.getLogger(service_name)
    logger.setLevel(getattr(logging, settings.log_level.upper()))

    # Consoler Handler
    handler = logging.StreamHandler(sys.stdout) # log to console
    handler.setLevel(logging.DEBUG)

    # Format: timestamp - service - level - message
    formatter = logging.Formatter(
        fmt="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S" 
    )
    handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(handler)

    return logger