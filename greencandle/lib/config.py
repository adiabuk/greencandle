#!/usr/bin/env python
#pylint: disable=protected-access

"""
Get values from config file
"""
from configparser import ConfigParser
import numpy
from .logger import getLogger
from .common import AttributeDict

def create_config():
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
