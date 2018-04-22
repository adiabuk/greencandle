#pylint: disable=invalid-name,global-statement

"""
Generic logging class for greencandle modules
"""

import sys
import logging
import traceback
from lib.config import get_config

def getLogger(logger_name=None):
    """
    Get Customized logging instance
        Args:
            logger_name: name of module
        Returns:
            logging instance with formatted handler
        """

    logging_level = int(get_config("logging")["level"])
    logger = logging.getLogger(logger_name)
    if not logger.handlers:
        logger.setLevel(logging_level)
        ch = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s;%(levelname)s;%(name)s;%(message)s",
                                      "%Y-%m-%d %H:%M:%S")
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger


def get_decorator(errors=(Exception,)):
    logger = getLogger(__name__)
    def decorator(func):

        def new_func(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except errors:
                logger.critical("Got Error " + str(sys.exc_info()))
                raise

        return new_func

    return decorator
