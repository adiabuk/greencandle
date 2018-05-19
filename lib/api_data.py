#!/usr/bin/env python

"""
Get buy/sell triggers from local API
"""

import json
import time
from urllib.request import urlopen
from lib.mysql import Mysql
import binance

def get_change(pair, interval="5m"):
    """
    Get buy/sell triggers
    """
    url = "http://127.1:5001/data"
    data = urlopen(url).read().decode("utf-8")
    json_data = json.loads(str(data))
    dbase = Mysql(test=False, interval=interval)
    trades = dbase.get_trades()
    prices = binance.prices()

    current_price = float(prices[pair])
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    try:
        value = json_data[pair]
    except KeyError:  # FIXME
        return "hold", current_time, current_price


    if "Sell" in value and pair in trades:
        # sell item
        buy_price = dbase.get_trade_value(pair)[0][0]
        if current_price > buy_price:
            return "sell", current_time, current_price

    elif "Buy" in value and pair not in trades:
        return "buy", current_time, current_price
    return "hold", current_time, current_price
