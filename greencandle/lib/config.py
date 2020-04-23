#!/usr/bin/env python
#pylint: disable=protected-access,consider-iterating-dictionary

"""
Get values from config file
"""
from configparser import ConfigParser
import sys
import numpy
from .common import AttributeDict


REQUIRED_CONFIG = {'database':['db_host', 'db_user', 'db_password', 'db_database'],
                   'email': ['email_from', 'email_to', 'email_password', 'email_active'],
                   'redis': ['redis_host', 'redis_port', 'redis_expire', 'redis_expiry_seconds'],
                   'push': ['push_host', 'push_channel', 'push_active'],
                   'main': ['logging_level', 'max_trades', 'divisor', 'binance_api_key', 'name',
                            'binance_api_secret', 'coinbase_api_key', 'buy_rule1',
                            'wait_between_trades', 'time_between_trades', 'logging_output',
                            'coinbase_api_secret', 'interval', 'sell_rule1',
                            'drain', 'no_of_klines', 'pairs', 'stop_loss_perc',
                            'take_profit', 'take_profit_perc', 'indicators', 'rate_indicator',
                            'trailing_stop_loss', 'trailing_stop_loss_perc']}

def create_config():
    """
    Read config file and return required config
    Args:
        test: boolean - will determine if "main" will be backend or test
    Return
        None: sections will be added to globals() by section and be available module-wide
    """
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
    for key in REQUIRED_CONFIG.keys():
        try:
            list_1 = list(globals()[key].keys())
        except KeyError:
            missing_section.append(key)
            continue
        list_2 = REQUIRED_CONFIG[key]
        missing_list.extend(list(numpy.setdiff1d(list_2, list_1, assume_unique=True)))
    config = True
    for section in REQUIRED_CONFIG.keys():
        for key in list(globals()[section]):
            if globals()[section][key] == '':
                # delete empty keys
                globals()[section].pop(key, None)
    if missing_list:
        print('error, missing config', missing_list)
        config = False
    if missing_section:
        print('error, missing section', missing_section)
        config = False
    return config
