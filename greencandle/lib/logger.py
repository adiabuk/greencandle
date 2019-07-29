#pylint: disable=invalid-name,global-statement

"""
Generic logging class for greencandle modules
"""

import sys
import logging

def getLogger(logger_name=None):
    """
    Get Customized logging instance
        Args:
            logger_name: name of module
        Returns:
            logging instance with formatted handler
        """

    logging_level = 20
    logger = logging.getLogger(logger_name)
    if logger.hasHandlers():
        logger.handlers.clear()

    logger.setLevel(logging_level)
    logger.propagate = False
    ch = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s",
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
                logger.critical("Got Error %s", str(sys.exc_info()), errors)
                #logger.critical('Function', method.__name__, 'time:', round((te -ts)*1000,1), 'ms')

                raise

        return new_func

    return decorator
