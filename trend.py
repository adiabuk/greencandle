#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
# pylint: disable=unused-argument

"""
Get Supertrend values and trigger points for traing pair
"""

from __future__ import print_function
import argparse
import os
import sys
import json
import csv
import time
import pandas
import argcomplete
import binance
from indicator import SuperTrend, RSI
from morris import KnuthMorrisPratt
import order

HOME_DIR = os.path.expanduser('~')
CONFIG = json.load(open(HOME_DIR + '/.binance'))
API_KEY = CONFIG['api_key']
API_SECRET = CONFIG['api_secret']

def get_binance_dataframe(pair, interval):
    """
    Get pandas dataframe from binance data
    """
    try:
        raw = binance.klines(pair, interval)
    except IndexError:
        sys.stderr.write("Unable to fetch data for " + pair + "\n")
        sys.exit(2)
    dataframe = pandas.DataFrame(raw, columns=['openTime', 'open', 'high', 'low',
                                               'close', 'volume'])
    return dataframe

def get_rsi(pair="XRPETH"):
    """ get RSI oscillator values """
    dataframe = get_binance_dataframe(pair, "3m")
    columns = ["date", "Open", "High", "Low", "Close", "Volume"]  # rename columns
    for index, item in enumerate(columns):
        dataframe.columns.values[index] = item

    mine = dataframe.apply(pandas.to_numeric)
    rsi = RSI(mine)
    df_list = rsi['RSI_21'].tolist()
    df_list = ["%.1f" % float(x) for x in df_list]
    return df_list[-10:]

def get_supertrend(pair="XRPETH"):
    """ get the super trend values """
    dataframe = get_binance_dataframe(pair, "3m")
    columns = ["date", "Open", "High", "Low", "Close", "Volume"]  # rename columns
    for index, item in enumerate(columns):
        dataframe.columns.values[index] = item

    mine = dataframe.apply(pandas.to_numeric)
    supertrend = SuperTrend(mine, 10, 3)
    df_list = supertrend['STX_10_3'].tolist()
    return df_list[-10:]

def find_pattern(result, pattern):
    """
    Find Buy/Sell pattern in supertrend supertrend
    """
    pass

def append_to_csv(fields):
    """
    Append list of outputs to a csv file
    """
    with open(HOME_DIR + '/triggers.csv', 'a') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(fields)

def main():
    """ Main function """
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--no_csv', action='store_true', default=False)
    parser.add_argument('-p', '--pair')
    parser.add_argument('-i', '--interval')
    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    while True:
        print("Fetching, ", time.time())
        fetch_loop(args.no_csv, trading_pair=args.pair, interval=args.interval)

def fetch_loop(write_csv=True, trading_pair=None, interval="3m"):
    """
    Loop over available trading pairs and find buy/sell triggers
    """
    if trading_pair:
        pairs = [trading_pair]
    else:
        pairs = [x for x in binance.prices().keys() \
                 if 'BTC' in x or 'ETH' in x]

    for pair in pairs:
        print("Looking up pair:", pair)
        supertrend = get_supertrend(pair)
        rsi = get_rsi(pair)

        if 7 in [s for s in KnuthMorrisPratt(supertrend, ["down", "up", "up"])]:
            action = "BUY"
            price = order.get_buy_price(pair)
        elif 8 in [s for s in KnuthMorrisPratt(supertrend, ["up", "down"])]:
            action = "SELL"
            price = order.get_sell_price(pair)
        else:
            action = "HOLD"
            price = binance.prices()[pair]
        if action == "BUY" or action == "SELL" or action == "HOLD":
            output = (str(pair), str(rsi), str(supertrend), str(action),
                      str(time.time()), str(price))
            print(output)

            if write_csv:
                append_to_csv(output)

if __name__ == "__main__":
    main()
