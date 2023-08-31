#pylint: disable=no-member

"""Get account value from binance and coinbase """

from __future__ import print_function
from requests.exceptions import ReadTimeout
from greencandle.lib import config
from greencandle.lib.binance_accounts import get_binance_spot, get_binance_cross, \
        get_binance_isolated
from greencandle.lib.coinbase_accounts import get_coinbase_values
from greencandle.lib.phemex_accounts import get_phemex_values
from greencandle.lib.mysql import Mysql
from greencandle.lib.logger import get_logger

config.create_config()
LOGGER = get_logger(__name__)

class Balance(dict):
    """
    Class to add/retrieve balance to/from mysql db
    """
    def __init__(self, test):
        self.dbase = Mysql(test=test, interval='1h')
        super().__init__()

    def __del__(self):
        del self.dbase

    def save_balance(self, prices):
        """Save balances to db"""

        # Add scheme to DB
        self.dbase.insert_balance(prices)

    @staticmethod
    def get_empty_values(strategy):
        """
        Return placeholder empty dict to keep DB row numbers in sync between balance writes
        """
        return {strategy: {'TOTALS': {'BTC': 0, 'USD': 0, 'GBP': 0, 'count': 'N/A'}}}

    def get_balance(self, coinbase=False, margin=True, phemex=False, isolated=False):
        """
        get dict of all balances

        Args:
            None

        Returns:
            dict of balances for each coin owned in binance (spot/margin)
            and coinbase/phemex

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
        binance = get_binance_spot()
        combined_dict = binance.copy()   # start with binance"s keys and values

        if phemex:
            phemex = get_phemex_values()
            combined_dict.update(phemex)
        else:
            phemex = self.get_empty_values('phemex')
            combined_dict.update(phemex)

        if coinbase:
            try:
                coinbase = get_coinbase_values()
            except ReadTimeout:
                LOGGER.critical("Unable to get coinbase balance")
                coinbase = {}
            combined_dict.update(coinbase)   # modifies z with y"s keys and values & returns None
        else:
            coinbase = self.get_empty_values('coinbase')
            combined_dict.update(coinbase)

        if margin:
            margin = get_binance_cross()
            combined_dict.update(margin)
        else:
            margin = self.get_empty_values('margin')
            combined_dict.update(margin)

        if isolated:
            isolated = get_binance_isolated()
            combined_dict.update(isolated)
        else:
            isolated = self.get_empty_values('isolated')
            combined_dict.update(isolated)

        return combined_dict

    @staticmethod
    def check_balance(balance):
        """
        Check if balance dictionary is valid
        """
        for key, val in balance.items():
            for item in ['USD', 'GBP', 'BTC', 'count']:
                if not item in val.keys() or balance[key][item] == '':
                    return False
            return True


    def get_saved_balance(self, balance=None):
        """print live balance"""

        phemex = config.accounts.account2_type == 'phemex'
        bal = balance if balance else self.get_balance(phemex=phemex)

        for key, val in bal.items():
            result = self.check_balance(val)
            if not result:
                LOGGER.info("Error: invalid balance entry for %s", key)

        binance_usd = bal['margin']['TOTALS']['USD'] + bal['binance']['TOTALS']['USD'] + \
                      bal['isolated']['TOTALS']['USD']
        binance_btc = bal['margin']['TOTALS']['BTC'] + bal['binance']['TOTALS']['BTC'] + \
                      bal['isolated']['TOTALS']['BTC']
        if phemex:
            phemex_usd = bal['phemex']['TOTALS']['USD']
            phemex_btc = bal['phemex']['TOTALS']['BTC']
        else:
            phemex_btc = 0
            phemex_usd = 0
        totals_btc = float(binance_btc) + float(phemex_btc)
        totals_usd = float(binance_usd) + float(phemex_usd)

        balances = [f"Binance USD = ${binance_usd:,.2f}",
                    f"Binance BTC = ฿{round(binance_btc, 5)}",
                    f"Phemex USD = ${phemex_usd:,.2f}",
                    f"Phemex BTC = ฿{round(phemex_btc, 5)}",
                    f"TOTAL USD = ${totals_usd:,.2f}",
                    f"TOTAL BTC = ฿{round(totals_btc, 5)}"]

        bal_str = '\n'.join(balances) + '\n'
        return bal_str
