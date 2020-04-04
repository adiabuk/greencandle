#pylint: disable=no-member,unused-import

"""Get account value from binance and coinbase """

from __future__ import print_function
import json
from requests.exceptions import ReadTimeout
from . import config
from .binance_accounts import get_binance_values, get_binance_margin
from .coinbase_accounts import get_coinbase_values
from .mysql import Mysql
from .logger import get_logger

LOGGER = get_logger(__name__)

class Balance(dict):
    """
    Class to add/retrieve balance to/from mysql db
    """
    def __init__(self, test, *args, **kwargs):
        self.dbase = Mysql(test=test, interval='1h')
        super(Balance, self).__init__(*args, **kwargs)

    def __del__(self):
        del self.dbase

    def save_balance(self, prices):
        """Save balances to db"""

        # Add scheme to DB
        self.dbase.insert_balance(prices)

    @staticmethod
    def get_balance(coinbase=False, margin=False):
        """
        get dict of all balances

        Args:
            None

        Returns:
            dict of balances for each coin owned in binance (spot/margin)
            and coinbase

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

        binance = get_binance_values()
        combined_dict = binance.copy()   # start with binance"s keys and values
        if coinbase:
            try:
                coinbase = get_coinbase_values()
            except ReadTimeout:
                LOGGER.critical("Unable to get coinbase balance")
                coinbase = {}
            combined_dict.update(coinbase)   # modifies z with y"s keys and values & returns None
        if margin:
            margin = get_binance_margin()
            combined_dict.update(margin)

        return combined_dict

    def get_saved_balance(self):
        """print live balance"""
        print(json.dumps(self.get_balance(), indent=4))
