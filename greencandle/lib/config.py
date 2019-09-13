#!/usr/bin/env python
#pylint: disable=protected-access,consider-iterating-dictionary

"""
Get values from config file
"""
from configparser import ConfigParser
import sys
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

    logger.info('Getting config')
    parser = ConfigParser()
    parser.read("/etc/greencandle.ini")

    for section in parser.sections():
        globals()[section] = AttributeDict(parser._sections[section])
    if not check_config():
        sys.exit("Missing config")

def check_config():
    """
    Check config contains required sections and keys.
    Return True if all expected elements are present, otherwise return False
    """

    missing_list = []
    missing_section = []
    required_config = {'database':['host', 'user', 'password', 'db'],
                       'email': ['from', 'to', 'password'],
                       'redis': ['host', 'port', 'expire'],
                       'push': ['host', 'channel'],
                       'main': ['logging_level', 'max_trades', 'binance_api_key',
                                'binance_api_secret', 'coinbase_api_key', 'buy_rule1',
                                'coinbase_api_secret', 'interval', 'sell_rule1',
                                'drain', 'no_of_klines', 'pairs', 'stop_loss_perc',
                                'take_profit_perc', 'indicators', 'rate_indicator']}

    for key in required_config.keys():
        try:
            list_1 = list(globals()[key].keys())
        except KeyError:
            missing_section.append(key)
            continue
        list_2 = required_config[key]
        missing_list.extend(list(numpy.setdiff1d(list_2, list_1, assume_unique=True)))
    config = True
    if missing_list:
        print('error, missing config', missing_list)
        config = False
    if missing_section:
        print('error, missing section', missing_section)
        config = False
    return config
