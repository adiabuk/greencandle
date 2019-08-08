#!/usr/bin/env python

"""Get account value from binance and coinbase """

from __future__ import print_function
import json

from . import config
from requests.exceptions import ReadTimeout
from .binance_accounts import get_binance_values
from .coinbase_accounts import get_coinbase_values
from .mysql import Mysql
from .logger import getLogger
from . import config

LOGGER = getLogger(__name__, config.main.logging_level)

def get_balance(test=False, interval="5m", coinbase=False):
    """
    get dict of all balances

    Args:
        None

    Returns:
        dict of balances for each coin owned in binance and coinbase
        Example structure is as follows:
        {
    "binance": {
        "GAS": {
            "count": 0.000225,
            "GBP": 0.004446673853759101,
            "BTC": 6.32025e-07,
            "USD": 0.00616831119
        },
        "TOTALS": {
            "count": "",
            "GBP": 263.96417114971814,
            "BTC": 0.037518370080113994,
            "USD": 366.1642846338805
        },
        "PPT": {
            "count": 1.0,
            "GBP": 12.382652557440002,
            "BTC": 0.00176,
            "USD": 17.176896000000003
        },
    "coinbase":
        "BTC": {
            "count": "",
            "GBP": 26.96417114971814,
            "BTC": 0.0037518370080113994,
            "USD": 36.1642846338805
        },
        "TOTALS": {
            "count": "",
            "GBP": 26.96417114971814,
            "BTC": 0.0037518370080113994,
            "USD": 36.1642846338805
        }
    }

    """

    dbase = Mysql(test=test, interval="5m")
    binance = get_binance_values()
    if coinbase:
        try:
            coinbase = get_coinbase_values()
        except ReadTimeout:
            LOGGER.critical("Unable to get coinbase balance")
            coinbase = {}
        combined_dict = binance.copy()   # start with binance"s keys and values
        combined_dict.update(coinbase)    # modifies z with y"s keys and values & returns None
    else:
        combined_dict = binance

    dbase.insert_balance(combined_dict)
    del dbase
    return combined_dict

def main():
    """print formated json of dict when called directly """
    print(json.dumps(get_balance(), indent=4))

if __name__ == "__main__":
    main()
