#!/usr/bin/env python

import os
import sys
import binance

BASE_DIR = os.getcwd().split("greencandle", 1)[0] + "greencandle"
sys.path.append(BASE_DIR)

from lib.auth import binance_auth
from lib.mysql import Mysql
from lib.profit import guess_profit


_, pair, interval, quantity = sys.argv
binance_auth()
dbase = Mysql(test=False, interval=interval)
trade =  dbase.get_trade_value(pair)
print(trade)
last_buy=trade[0][0]
last_quantity = trade[0][1]
prices = binance.prices()

new_price = prices[pair]
new_quantity = quantity


updated_price = ((float(last_buy) * float(last_quantity)) + (float(new_price) *
    float(new_quantity))) / (float(last_quantity) +
        float(new_quantity))
print(format(updated_price, ".20F"))

profit = guess_profit(updated_price, new_price, 20)
print(profit[0], profit[-1])
