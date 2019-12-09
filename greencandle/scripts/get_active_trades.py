#!/usr/bin/env python
#pylint: disable=wrong-import-position,no-member

"""
Get details of current trades using mysql and current value from binance
"""

import binance

from ..lib.mysql import Mysql
from ..lib import config

config.create_config()
from ..lib.auth import binance_auth
from ..lib.logger import getLogger

LOGGER = getLogger(__name__, config.main.logging_level)

def main():
    """ Main function """
    prices = binance.prices()
    binance_auth()
    dbase = Mysql()

    dbase.run_sql_query("delete from open_trades")
    trades = dbase.fetch_sql_data("select pair, buy_time, buy_price, name from trades where "
                                  "sell_price is NULL", header=False)
    for trade in trades:
        try:
            pair, buy_time, buy_price, name = trade
            current_price = prices[pair]
            perc = 100 * (float(current_price) - float(buy_price)) / float(buy_price)
            insert = ('insert into open_trades (pair, buy_time, buy_price, current_price, '
                      'perc, name) VALUES ("{0}", "{1}", "{2}", "{3}", "{4}", "{5}")'
                      .format(pair, buy_time, buy_price, current_price, perc, name))

            dbase.run_sql_query(insert)
        except ZeroDivisionError:
            LOGGER.critical("%s has a zero buy price, unable to calculate percentage", pair)

if __name__ == "__main__":
    main()
