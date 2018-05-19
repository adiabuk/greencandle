#!/usr/bin/env python

"""
Get buy/sell triggers from local API
"""

import datetime
import json
import time
from urllib.request import urlopen
import binance
from lib.mysql import Mysql
from lib.logger import getLogger


LOGGER = getLogger(__name__)

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

    if pair in trades:
        trade_value = dbase.get_trade_value(pair)[0]
        buy_price = trade_value[0]
        buy_time = trade_value[2]

        if float(current_price) > (float(buy_price) * ((1/100)+1)) and \
                buy_time < datetime.datetime.now() - datetime.timedelta(hours=5):
            LOGGER.info("SELL 5hrs %s %s", format(current_price, ".20f"), pair)
            return "sell", current_time, current_price
        elif float(current_price) > (float(buy_price) * ((4/100)+1)):
            LOGGER.info("SELL 4 %s %s", format(current_price, ".20f"), pair)
            return "sell", current_time, current_price
        elif "Sell" in value and pair in trades:
            if float(current_price) > (float(buy_price)):
                LOGGER.info("SELL direction change %s %s", format(current_price, ".20f"), pair)
                return "sell", current_time, current_price

            elif float(current_price) < float(buy_price) * (1- (2/100)):  # 2% stop loss
                LOGGER.info("SELL stoploss %s %s", format(current_price, ".20f"), pair)
                return "sell", current_time, current_price

    elif "Buy" in value and pair not in trades and not dbase.is_recent_sell(pair):
        LOGGER.info("BUY %s %s", format(current_price, ".20f"), pair)
        return "buy", current_time, current_price
    return "hold", current_time, current_price
