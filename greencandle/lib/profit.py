#!/usr/bin/env python
#pylint: disable=wrong-import-order
"""
Calculate potential profits from historical data
"""

from __future__ import print_function
from collections import defaultdict
from greencandle.lib.mysql import Mysql
from greencandle.lib.common import sub_perc, perc_diff

RATE = 0.00014 # GBP to BTC
FEES = 0.05

def get_quantity(open_price, total_open_btc):
    """get amount to open with"""
    total_open_btc = sub_perc(FEES, total_open_btc)   # Subtract trading fees
    amount = total_open_btc / open_price
    return amount

def guess_profit(open_price, close_price, investment_gbp):
    """
    Get profit prediction based on initial GBP investment and open/close prices of currency pair

    Args:
        open_price
        close_price
        investment_gbp

    Returns: tuple contiaing the following:
        profit
        amount
        difference
        perc
    """
    open_price = float(open_price)
    close_price = float(close_price)

    total_open_btc = investment_gbp * RATE
    total_open_btc = sub_perc(FEES, total_open_btc)   # Subtract trading fees
    amount = total_open_btc / open_price

    total_close_btc = close_price * amount
    total_close_btc = sub_perc(FEES, total_close_btc)  # Subtract trading fees

    difference = total_close_btc - total_open_btc
    profit = difference * (1 / RATE)
    perc = perc_diff(open_price, close_price)
    return profit, amount, difference, perc

def get_recent_profit(interval=None, test=False):
    """
    calulate profit from aggregrate of recent transaction profits
    Args:
        test boolean (optional) - use test db if True, otherwise use live
        interval: (string, eg. 15m, 5m, 3m, 1m
    Returns:
        * total profit for all completed trades recorded (float)
        * sum of profit for each day (or partial day) recorded (dict)
            - where key is a string contiaining a date in the following format: yyyy-mm-dd
            - and value is a float containing th profit for given day

    """
    profits = []
    profit_dict = defaultdict(float)  #will allow us to increment unitilaized value (start at 0)
    dbase = Mysql(test=test, interval=interval)
    trades = dbase.get_last_trades()# contains tuple db results
    del dbase

    for trade in trades:  # each individual trade contains open_price, close_price, and inventment
        # items contained in tupple are as follows:
        # close_time, open_price, close_price, and investment

        # Remove the time from the datetime stamp
        # format is 'yyyy-mm-dd hh-mm-ss'
        # split on whitespace and replace with first portion only
        # This is done so that we can group by day and sum up profits
        day = str(trade[0]).split()[0]
        amount = float(trade[1]) * float(trade[3])/RATE
        profit_per_trade = guess_profit(float(trade[1]),
                                        float(trade[2]),
                                        amount)[0]  # get first item from function (profit)
        profits.append(profit_per_trade)
        profit_dict[day] += float(profit_per_trade)  # trade[0] is a date: yyyy-mm-dd

    return sum(profits), dict(profit_dict)
