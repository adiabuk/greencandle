#pylint: disable=no-member,arguments-differ,too-few-public-methods,inconsistent-return-statements

"""
Generic logging class for greencandle modules
"""

import logging
import traceback
from cysystemd.journal import JournaldLogHandler
from greencandle.lib import config
from greencandle.lib.alerts import send_slack_message

config.create_config()

class OneLineFormatter(logging.Formatter):
    """logging formatter for exceptions"""
    def formatException(self, exc_info):
        result = super().formatException(exc_info)
        return repr(result)

    def format(self, record):
        result = super().format(record)
        if record.exc_text or isinstance(record, str):
            result = result.replace("\n", "")
        return result

class AppFilter(logging.Filter):
    """
    Add module_name as well as app_name for journald logging
    """

    def __init__(self, module_name, *args, **kwargs):
        self.module_name = module_name
        super(AppFilter, self).__init__(*args, **kwargs)

    def filter(self, record):
        record.app_name = self.module_name
        return True

class NotifyOnCriticalStream(logging.StreamHandler):
    """
    Stream handler to send notifications on error or critical
    """
    def emit(self, record):
        super().emit(record)
        if record.levelno in (logging.ERROR, logging.CRITICAL):
            message = self.format(record)
            send_slack_message('alerts', message)

class NotifyOnCriticalJournald(JournaldLogHandler):
    """
    Journald handler to send notification on error or critical
    """
    def emit(self, record):
        """
        Change name from module name to app name from config
        """
        record.name = config.main.name
        super().emit(record)
        if record.levelno in (logging.ERROR, logging.CRITICAL):
            message = self.format(record)
            send_slack_message('alerts', message)

def get_logger(module_name=None):
    """
    Get Customized logging instance
      Args:
        logger_name: name of module
      Returns:
        logging instance with formatted handler
    """

    if config.main.logging_output == "journald":
        name = module_name
        handler = NotifyOnCriticalJournald()
        formatter = OneLineFormatter('[%(levelname)s] %(app_name)s %(message)s')
        handler.setFormatter(formatter)
    else:
        name = module_name.split('.')[-1]
        handler = NotifyOnCriticalStream()
        formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s",
                                      "%Y-%m-%d %H:%M:%S")
        handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.setLevel(int(config.main.logging_level))
    logger.propagate = False
    logger.addFilter(AppFilter(module_name=module_name))

    logger.addHandler(handler)
    return logger

def exception_catcher(errors=(Exception,)):
    """logging decorator"""
    logger = get_logger(__name__)
    def decorator(func):

        def new_func(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except errors:
                logger.exception(traceback.format_exc())

        return new_func

    return decorator
