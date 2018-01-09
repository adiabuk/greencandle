#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
#pylint: disable=no-member

"""
Get ohlc (Open, High, Low, Close) values from given cryptos
and detect trends using candlestick patterns

"""

from __future__ import print_function
import json
import os
import sys
import argparse
import time
import calendar
import pandas
import numpy
import binance
import talib
import argcomplete
from graph import create_graph

HOME_DIR = os.path.expanduser('~')
CONFIG = json.load(open(HOME_DIR + '/.binance'))
API_KEY = CONFIG['api_key']
API_SECRET = CONFIG['api_secret']

binance.set(API_KEY, API_SECRET)

def make_float(arr):
    """Convert dataframe array into float array"""
    return numpy.array([float(x) for x in arr.values])

def get_details(pair, args):
    """ Get details from binance API """

    red = "\033[31m"
    white = "\033[0m"
    raw = binance.klines(pair, "1m")
    epoch = calendar.timegm(time.gmtime())
    dataframe = pandas.DataFrame.from_dict(raw)

    ohlc = (make_float(dataframe.open),
            make_float(dataframe.high),
            make_float(dataframe.low),
            make_float(dataframe.close))

    # LAST 10 items
    hammer = talib.CDLHAMMER(*ohlc)[-10:]
    invhammer = talib.CDLINVERTEDHAMMER(*ohlc)[-10:]
    engulf = talib.CDLENGULFING(*ohlc)[-10:]
    doji = talib.CDLDOJI(*ohlc)[-10:]
    yield "HAMMER", hammer
    yield "INVHAMMER", invhammer
    yield "ENGULF", engulf
    yield "DOJI", doji
    yield "https://uk.tradingview.com/symbols/{0}/".format(pair)
    sys.stdout.write(red)
    if hammer[-1] == 100:
        yield "BUY ", pair, epoch
    elif invhammer[-1] == 100:
        yield "SELL ", pair, epoch
    elif engulf[-1] == 100:
        yield "BUY ", pair, epoch
    elif engulf[-1] == -100:
        yield "SELL", pair, epoch
    elif doji[-1] == 100:
        yield "INVESTIGATE", pair, epoch
    else:
        yield "HOLD ", pair, epoch
    sys.stdout.write(white)

    if args.graph:
        #unhash to see graph
        create_graph(dataframe, pair)

def main():
    """ main function """
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--graph', action='store_true', default=False)
    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    pairs = ["XRPBTC", "XRPETH", "MANABTC", "PPTBTC", "MTHBTC", "BNBBTC", "BNBETH", "ETHBTC"]
    #pairs =  [x for x in binance.prices().keys() if 'BTC' in x]

    for pair in pairs:
        #PAIR = "XRPBTC"
        #PAIR = "XRPETH"
        #PAIR = "MANABTC"
        for data in get_details(pair, args):
            print(*data)

if __name__ == '__main__':
    main()
