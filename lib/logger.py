#pylint: disable=invalid-name,global-statement

"""
Generic logging class for greencandle modules
"""


import logging

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
