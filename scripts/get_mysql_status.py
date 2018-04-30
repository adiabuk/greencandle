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
a = Mysql(test=False, interval=sys.argv[1])

trades = a.get_trades()

for trade in trades:
  current_price = float(prices[trade])
  buy_price = float(a.get_trade_value(trade)[0])
  perc = 100 * (current_price - buy_price) / buy_price
  print(trade, buy_price, current_price, float(current_price) > (buy_price), perc)

