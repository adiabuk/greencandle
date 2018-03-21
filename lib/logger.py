#pylint: disable=invalid-name,global-statement

"""
Generic logging class for greencandle modules
"""

import sys
import logging
import traceback

def getLogger(logger_name=None):
    """
    Get Customized logging instance
        Args:
            logger_name: name of module
        Returns:
            logging instance with formatted handler
        """

    logger = logging.getLogger(logger_name)
    if not logger.handlers:
        logger.setLevel(logging.DEBUG)
        ch = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s;%(levelname)s;%(name)s;%(message)s",
                                      "%Y-%m-%d %H:%M:%S")
        ch.setFormatter(formatter)
        logger.addHandler(ch)
    return logger

logger = getLogger(__name__)

def get_decorator(errors=(Exception, ), default_value=''):

    def decorator(func):

        def new_func(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except errors as e:
                logger.critical("Got Error " + str(sys.exc_info()))
                #traceback.print_stack()
                raise
                #return 1 #default_value
                return ""

        return new_func

    return decorator

