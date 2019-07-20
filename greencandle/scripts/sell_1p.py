#!/usr/bin/env python
#pylint: disable=wrong-import-position

"""
Sell any open orders for given interval which has over 1% profit
"""

import os
import sys
import time
import binance

BASE_DIR = os.getcwd().split("greencandle", 1)[0] + "greencandle"
sys.path.append(BASE_DIR)

from ..lib.mysql import Mysql
from ..lib.order import sell
from ..lib.profit import guess_profit

def main():
    interval = sys.argv[1]
    prices = binance.prices()
    sells = []
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    dbase = Mysql(test=False, interval=interval)

    for trade in dbase.get_trades():
        value = dbase.get_trade_value(trade)
        buy_price = value[0][0]
        amount = value[0][1]
        current_price = prices[trade]
        perc = float(guess_profit(float(buy_price), float(current_price), float(amount))[-1])
        if perc > 1:
            print("sell", trade)
            sells.append((trade, current_time, current_price))

    if sells:
        sell(sells, False, False, interval)

main()
