#pylint: disable=no-member,

"""Get account value from binance and coinbase """

from __future__ import print_function
import json
import binance
from . import config
from requests.exceptions import ReadTimeout
from .binance_accounts import get_binance_values
from .coinbase_accounts import get_coinbase_values
from .mysql import Mysql
from .logger import getLogger

LOGGER = getLogger(__name__, config.main.logging_level)

class Balance(dict):
    def __init__(self, interval, test=False, *args, **kwargs):
        self.db = Mysql(test=test, interval=interval)
        self.interval = interval
        self.balance = get_balance(test=test)
        super(Balance, self).__init__(*args, **kwargs)


    def __del__(self):
        del self.db

    def save_balance(self, prices):
        # Save balances to db
        scheme = {}
        if not self.test:
            #  Add prices for current symbol to scheme
            #trade = Trade(interval=self.interval, test=self.test)
            #prices = {"buy": trade.get_buy_price(), "sell": trade.get_sell_price(),
            #          "market": binance.prices()[pair]}
            scheme.update(prices)

            bal = self.balance["binance"]["TOTALS"]["GBP"]

            # Add scheme to DB
            try:
                self.db.insert_data(interval=self.interval,
                                    symbol=scheme["symbol"], event=scheme["event"],
                                    data=scheme["data"],
                                    resistance=str(scheme["resistance"]),
                                    support=str(scheme["support"]), buy=str(scheme["buy"]),
                                    sell=str(scheme["sell"]), market=str(scheme["market"]),
                                    balance=str(bal))
            except Exception as excp:
                LOGGER.critical("AMROX25 Error: %s", str(excp))

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
