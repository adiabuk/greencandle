#pylint: disable=protected-access,consider-iterating-dictionary

"""
Get values from config file
"""
from configparser import ConfigParser
import numpy
from greencandle.lib.common import AttributeDict


REQUIRED_CONFIG = {'database':['db_host', 'db_user', 'db_password', 'db_database'],
                   'email': ['email_from', 'email_to', 'email_password', 'email_active'],
                   'redis': ['redis_host', 'redis_port', 'redis_expiry_seconds'],
                   'slack': ['url'],
                   'accounts': [],
                   'main': ['logging_level', 'max_trades', 'divisor', 'name', 'open_rule1',
                            'wait_between_trades', 'time_between_trades', 'logging_output',
                            'interval', 'close_rule1', 'drain', 'no_of_klines', 'pairs',
                            'stop_loss_perc', 'take_profit_perc', 'indicators',
                            'trailing_stop_loss_perc', 'time_in_trade', 'immediate_stop',
                            'immediate_trailing_stop', 'immediate_take_profit']}

def create_config():
    """
    Read config file and return required config
    Args:
        test: boolean - will determine if "main" will be backend or test
    Return
        None: sections will be added to globals() by section and be available module-wide
    """
    parser = ConfigParser(allow_no_value=True)
    parser.read("/etc/greencandle.ini")

    for section in parser.sections():
        globals()[section] = AttributeDict(parser._sections[section])
    check_config()
    # sort account details
    for i in range(1, 5):
        if f'account{i}_type' in globals()['accounts']:
            account_type = globals()['accounts'][f'account{i}_type']
            key = globals()['accounts'][f'account{i}_key']
            secret = globals()['accounts'][f'account{i}_secret']
            if account_type not in globals()['accounts']:
                globals()['accounts'][account_type] = []
            globals()['accounts'][account_type].append({'key':key, 'secret':secret})

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
        for key in REQUIRED_CONFIG[section]:
            if globals()[section][key] == '':
                # delete empty keys
                missing_section.append(key)
                globals()[section].pop(key, None)
    if missing_list:
        raise AttributeError(f'error, missing config {missing_list}')
    if missing_section:
        raise AttributeError(f'error, missing section {missing_section}')
    return config
