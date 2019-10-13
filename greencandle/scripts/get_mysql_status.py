#!/usr/bin/env python
#pylint: disable=wrong-import-position
"""
Get details of current trades using mysql and current value from binance
"""

import json
import sys

from operator import itemgetter
import binance

from ..lib.mysql import Mysql
from ..lib import config

test = True if sys.argv[2].lower() == "test" else False
config.create_config()
from ..lib.auth import binance_auth

def main():
    """ Main function """
    prices = binance.prices()
    binance_auth()
    dbase = Mysql(test=test, interval=sys.argv[1])

    trades = dbase.get_trades()
    profits = []
    percs = []
    print("\033[1m") # BOLD
    print("pair buy_price current_price amount in_profit percentage profit")
    print("\033[0m") # END


    details = []
    for trade in trades:
        current_price = float(prices[trade])
        trade_details = dbase.get_trade_value(trade)
        buy_price = float(trade_details[0][0])
        amount = float(trade_details[0][1])
        profit = (current_price/0.00014*amount) - (buy_price/0.00014*amount)
        perc = 100 * (current_price - buy_price) / buy_price

        profits.append(profit)
        percs.append(perc)
        perc = float(format(perc, ".4f"))
        profit = float(format(profit, ".4f"))
        details.append((trade, format(float(buy_price), ".20f"),
                        format(float(current_price), ".20f"),
                        amount, current_price > buy_price, perc, profit))

    details = sorted(details, key=itemgetter(-2))
    for item in details:
        print("{0} {1} {2} {3} {4} {5} {6} {7}".format(*item))

    print("\nxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx\n\n\n\n")
    count = len(profits)
    count = 1 if count==0 else count
    print("Total_profit: {0} Avg_Profit: {1} Avg_Percs: {2} count: {3}".format(sum(profits),
                                                                               sum(profits)/count,
                                                                               sum(percs)/count,
                                                                               count))
if __name__ == "__main__":
    main()
