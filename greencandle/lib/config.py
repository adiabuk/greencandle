#!/usr/bin/env python
#pylint: disable=protected-access

"""
Get values from config file
"""

from configparser import ConfigParser
from .logger import getLogger, get_decorator
from .common import AttributeDict

def create_config(test=False):
    """
    Read config file and return required config
    Args:
        test: boolean - will determine if "main" will be backend or test
    Return
        None: sections will be added to globals() by section and be available module-wide
    """
    logger = getLogger(__name__)
    config = AttributeDict()
    logger.info('Getting config')
    parser = ConfigParser()
    parser.read("/etc/greencandle.ini")

    for section in parser.sections():
        globals()[section] = AttributeDict(parser._sections[section])
    if test:
        globals()['main'] = AttributeDict(parser._sections['test'])
    else:
        globals()['main'] = AttributeDict(parser._sections['backend'])
