#!/usr/bin/env python
"""
Calculate potential profits from historical data
"""

from __future__ import print_function
from collections import defaultdict
from forex_python.converter import CurrencyRates
import binance
from lib.mysql import Mysql
from lib.common import add_perc, sub_perc, perc_diff

CURRENCY = CurrencyRates()
RATE = 0.00014 # GBP to BTC
FEES = 0.05

def guess_profit(buy_price, sell_price, investment_gbp):
    """
    Get profit prediction based on initial GBP investment and buy/sell values of currency pair

    Args:
        buy_price
        sell_price
        investment_gbp

    Returns: tuple contiaing the following:
        profit
        amount
        difference
        perc
    """
    buy_price = float(buy_price)
    sell_price = float(sell_price)

    total_buy_btc = investment_gbp * RATE
    total_buy_btc = sub_perc(FEES, total_buy_btc)   # Subtract trading fees
    amount = total_buy_btc / buy_price

    total_sell_btc = sell_price * amount
    total_sell_btc = sub_perc(FEES, total_sell_btc)  # Subtract trading fees

    difference = total_sell_btc - total_buy_btc
    profit = difference * (1 / RATE)
    perc = perc_diff(buy_price, sell_price)
    return profit, amount, difference, perc

def get_recent_profit(test=False, interval="15m"):
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

    for trade in trades:  # each individual trade contains buy_price, sell_price, and inventment
        # items contained in tupple are as follows:
        # sell_time, buy_price, sell_price, and investment

        # Remove the time from the datetime stamp
        # format is 'yyyy-mm-dd hh-mm-ss'
        # split on whitespace and replace with first portion only
        # This is done so that we can group by day and sum up profits
        day = str(trade[0]).split()[0]
        profit_per_trade = guess_profit(float(trade[1]),
                                        float(trade[2]),
                                        float(trade[3]))[0]  # get first item from function (profit)
        profits.append(profit_per_trade)
        profit_dict[day] += float(profit_per_trade)  # trade[0] is a date: yyyy-mm-dd

    return sum(profits), dict(profit_dict)

def gbp_to_base(gbp, symbol):
    """
    50GBP => OMG
    50GBP => USD
    USD => BTC
    BTC => OMG
    """

    usd = gbp * CURRENCY.get_rate("GBP", "USD")
    btc = usd * float(binance.prices()["BTCUSDT"])
    omg = btc * float(binance.prices()[symbol + "BTC"])
    return format(omg, ".20f")

if __name__ == "__main__":
    print(gbp_to_base(50, "OMG"))
