#!/usr/bin/env python
#pylint: disable=wrong-import-position
"""
Get details of current trades using mysql and current value from binance
"""

import os
import json
import sys

from urllib.request import urlopen
from urllib.error import HTTPError
from operator import itemgetter
import binance

BASE_DIR = os.getcwd().split("greencandle", 1)[0] + "greencandle"
sys.path.append(BASE_DIR)
from ..lib.mysql import Mysql
from ..lib.auth import binance_auth


def main():
    prices = binance.prices()
    binance_auth()
    dbase = Mysql(test=False, interval=sys.argv[1])

    trades = dbase.get_trades()
    profits = []
    percs = []
    print("\033[1m") # BOLD
    print("pair buy_price current_price amount in_profit percentage profit direction")
    print("\033[0m") # END


    details = []
    url = "http://127.1:5001/data"
    try:
        data = urlopen(url).read().decode("utf-8")
    except HTTPError:
        data = []
        trades = []
        print("Waiting for API...")
    json_data = json.loads(str(data))
    for trade in trades:
        current_price = float(prices[trade])
        trade_details = dbase.get_trade_value(trade)
        buy_price = float(trade_details[0][0])
        amount = float(trade_details[0][1])
        profit = (current_price/0.00014*amount) - (buy_price/0.00014*amount)
        perc = 100 * (current_price - buy_price) / buy_price
        try:
            direction = json_data[trade]
        except KeyError:
            direction = "Unknown"
        profits.append(profit)
        percs.append(perc)
        perc = float(format(perc, ".4f"))
        profit = float(format(profit, ".4f"))

        details.append((trade, format(float(buy_price), ".20f"),
                        format(float(current_price), ".20f"),
                        amount, current_price > buy_price, perc, profit, direction))

    details = sorted(details, key=itemgetter(-2))
    for item in details:
        #sys.stdout.write(*item)
        print("{0} {1} {2} {3} {4} {5} {6} {7}".format(*item))
    print("\nxxx\n")
    count = len(profits)
    print("Total_profit: {0} Avg_Profit: {1} Avg_Percs: {2} count: {3}".format(sum(profits),
                                                                               sum(profits)/count,
                                                                               sum(percs)/count,
                                                                               count))
if __name__ == "__main__":
    main()
