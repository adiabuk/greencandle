#pylint: disable=invalid-name,global-statement,protected-access,no-member

"""
Generic logging class for greencandle modules
"""

import sys
import logging
from systemd.journal import JournaldLogHandler
from . import config

def getLogger(logger_name=None, logging_level=20):
    """
    Get Customized logging instance
        Args:
            logger_name: name of module
        Returns:
            logging instance with formatted handler
        """

    logger = logging.getLogger(logger_name)
    if logger.hasHandlers():
        logger.handlers.clear()

    logger.setLevel(int(config.main.logging_level))
    logger.propagate = False
    if config.main.logging_output == "journald":
        handler = JournaldLogHandler()
        #handler = logging.StreamHandler()
        formatter = logging.Formatter('[%(levelname)s] %(message)s')
        #formatter = logging.Formatter(logging.BASIC_FORMAT)
        handler.setFormatter(formatter)

    else:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(levelname)s %(name)s %(message)s")
        handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger

def get_decorator(errors=(Exception,)):
    """logging decorator"""
    logger = getLogger(__name__)
    def decorator(func):

        def new_func(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except errors:
                logger.critical("Got Error %s %s", str(sys.exc_info()), errors)
                #logger.critical('Function', method.__name__, 'time:', round((te -ts)*1000,1), 'ms')

                raise

        return new_func

    return decorator
