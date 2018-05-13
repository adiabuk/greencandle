#!/usr/bin/env python

"""
Get details of current trades using mysql and current value from binance
"""

import os
import sys
import binance

BASE_DIR = os.getcwd().split("greencandle", 1)[0] + "greencandle"
sys.path.append(BASE_DIR)
from lib.mysql import Mysql
from lib.auth import binance_auth

prices = binance.prices()
binance_auth()
dbase = Mysql(test=False, interval=sys.argv[1])

trades = dbase.get_trades()
profits = []
percs = []
for trade in trades:
    current_price = float(prices[trade])
    trade_details = dbase.get_trade_value(trade)
    buy_price = float(trade_details[0][0])
    amount = float(trade_details[0][1])
    profit = (current_price/0.00014*amount) - (buy_price/0.00014*amount)
    perc = 100 * (current_price - buy_price) / buy_price
    profits.append(profit)
    percs.append(perc)
    #print(trade, buy_price, current_price, current_price > buy_price, perc, profit)
    print("  pair:{0}, buy:{1}, current:{2}, amount:{3}, in_profit:{4}, perc:{5}, profit:{6}"
          .format(trade, buy_price, current_price, amount, current_price > buy_price, perc, profit))
print("Total profit: {0}, Avg Profit:{1}, Avg Perc: {2}".format(sum(profits),
                                                                sum(profits)/len(profits),
                                                                sum(percs)/len(percs)))
