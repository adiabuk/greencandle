#!/usr/bin/env python
#pylint: disable=wrong-import-position
"""
Get details of current trades using mysql and current value from binance
"""

import binance

from ..lib.mysql import Mysql
from ..lib import config

config.create_config()
from ..lib.auth import binance_auth

def main():
    """ Main function """
    prices = binance.prices()
    binance_auth()
    dbase = Mysql()

    dbase.run_sql_query("delete from open_trades")
    trades = dbase.fetch_sql_data("select pair, buy_time, buy_price from trades where "
                                  "sell_price is NULL", header=False)
    for trade in trades:
        pair = trade[0]
        print(pair)
        buy_time = trade[1]
        buy_price = trade[2]
        current_price = prices()[pair]
        perc = 100 * (float(current_price) - float(buy_price)) / float(buy_price)
        insert = ('insert into open_trades (pair, buy_time, buy_price, current_price, perc) '
                  'VALUES ("{0}", "{1}", "{2}", "{3}", "{4}")'.format(pair, buy_time,
                                                                      buy_price,
                                                                      current_price, perc))
        dbase.run_sql_query(insert)

if __name__ == "__main__":
    main()
