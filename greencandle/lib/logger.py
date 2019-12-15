#pylint: disable=no-member,arguments-differ

"""
Generic logging class for greencandle modules
"""

import logging
from systemd.journal import JournaldLogHandler
from . import config

class OneLineFormatter(logging.Formatter):
    """logging formatter for exceptions"""
    def formatException(self, exc_info):
        result = super().formatException(exc_info)
        return repr(result)

    def format(self, record):
        result = super().format(record)
        if record.exc_text:
            result = result.replace("\n", "")
        return result

def get_logger(logger_name=None):
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

        formatter = OneLineFormatter('[%(levelname)s] %(message)s')
        #formatter = logging.Formatter('[%(levelname)s] %(message)s')

        #formatter = logging.Formatter(logging.BASIC_FORMAT)
        handler.setFormatter(formatter)

    else:
        #handler = OneLineExceptionFormatter()
        handler = logging.StreamHandler()
        #formatter = logging.Formatter("%(levelname)s %(name)s %(message)s")
        #formatter = OneLineExceptionFormatter("%(levelname)s %(name)s %(message)s")
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s",
                                      "%Y-%m-%d %H:%M:%S")
        handler.setFormatter(formatter)

    logger.addHandler(handler)
    return logger

def get_decorator(errors=(Exception,)):
    """logging decorator"""
    logger = get_logger(__name__)
    def decorator(func):

        def new_func(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except errors:
                logger.exception("Got Error: ")   # %s %s", str(sys.exc_info()), errors)
                #logger.critical('Function', method.__name__, 'time:', round((te -ts)*1000,1), 'ms')

#                raise

        return new_func

    return decorator
