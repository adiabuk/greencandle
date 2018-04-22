#!/usr/bin/env python

import os
import sys
import binance

BASE_DIR = os.getcwd().split("greencandle", 1)[0] + "greencandle"
sys.path.append(BASE_DIR)

from lib.auth import binance_auth
from lib.mysql import Mysql

binance_auth()
mysql = Mysql(test=False, interval="5m")
balances = binance.balances()

holdings = []
mysql_holdings = mysql.get_trades()

for key, value in balances.items():
    if float(value['free']) > 0 or float(value['locked']) > 0 and "BTC" not in key:
        holdings.append(key + "BTC")

for item in holdings:
    try:
        x = binance.myTrades(item)[-1]
    except (IndexError, KeyError):
        print(item)
        continue
    try:
        buyer = x["isBuyer"]
    except (IndexError, KeyError):
        buyer = "Unknown"
    try:
        price = x["price"]
    except (IndexError, KeyError):
        price = "Unknown"
    try:
        quantity = x["qty"]
    except (IndexError, KeyError):
        quantity = "Unknown"
    try:
        current_price = binance.prices()[item]
    except (IndexError, KeyError):
        current_price = "Unknown"

    print(item, price, current_price, quantity, buyer, item in mysql_holdings, current_price > price)

