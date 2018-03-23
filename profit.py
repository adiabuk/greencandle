#!/usr/bin/env python
"""
Calculate potential profits from historical data
"""

from __future__ import print_function
from forex_python.converter import CurrencyRates
import binance
from lib.mysql import mysql

CURRENCY = CurrencyRates()
RATE = 0.00014 # GBP to BTC

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
    amount = total_buy_btc / buy_price

    total_sell_btc = sell_price * amount
    difference = total_sell_btc - total_buy_btc
    profit = difference *(1/RATE)
    perc = ((sell_price - buy_price)/buy_price)*100
    return profit, amount, difference, perc

def get_recent_profit(test=False):
    """
    calulate profit from aggregrate of recent transaction profits
    """
    profits = []
    dbase = mysql(test=test)
    trades = dbase.get_last_trades()  # contains tuple db results
    for trade in trades:  # each individual trade contains buy_price, sell_price, and inventment
        profits.append(guess_profit(float(trade[0]),
                                    float(trade[1]),
                                    float(trade[2]))[0])  # get first item
    return sum(profits)

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
    return "{0:.10f}".format(omg)

if __name__ == "__main__":
    print(gbp_to_base(50, "OMG"))
