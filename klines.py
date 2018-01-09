#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
#pylint: disable=no-member

import json
import os
import sys
import argparse
import pandas as pd
import numpy as np
import binance
import talib
import argcomplete
from graph import *
import time
import calendar

HOME_DIR = os.path.expanduser('~')
CONFIG = json.load(open(HOME_DIR + '/.binance'))
API_KEY = CONFIG['api_key']
API_SECRET = CONFIG['api_secret']

binance.set(API_KEY, API_SECRET)

def make_float(arr):
    """Convert dataframe array into float array"""
    return np.array([float(x) for x in arr.values])


def get_ohlc():
    raw = binance.klines(pair, "1m")

def get_details(pair, args):
    """ Get details from binance API """

    red = "\033[31m"
    white = "\033[0m"
    raw = binance.klines(pair, "1m")
    epoch = calendar.timegm(time.gmtime())
    df = pd.DataFrame.from_dict(raw)

    OHLC = (make_float(df.open), make_float(df.high), make_float(df.low), make_float(df.close))

    # LAST 10 items
    HAMMER = talib.CDLHAMMER(*OHLC)[-10:]
    INVHAMMER = talib.CDLINVERTEDHAMMER(*OHLC)[-10:]
    ENGULF = talib.CDLENGULFING(*OHLC)[-10:]
    DOJI = talib.CDLDOJI(*OHLC)[-10:]
    print "HAMMER", HAMMER
    print "INVHAMMER", INVHAMMER
    print "ENGULF", ENGULF
    print "DOJI", DOJI
    print "https://uk.tradingview.com/symbols/{0}/".format(pair)
    sys.stdout.write(red)
    if HAMMER[-1] == 100:
        print "BUY ", pair, epoch
    elif INVHAMMER[-1] == 100:
        print "SELL ", pair,epoch
    elif ENGULF[-1] == 100:
        print "BUY ", pair,epoch
    elif ENGULF[-1] == -100:
        print "SELL", pair,epoch
    elif DOJI[-1] == 100:
        print "INVESTIGATE", pair,epoch
    else:
        print "HOLD ", pair,epoch
    sys.stdout.write(white)

    if args.graph:
        #unhash to see graph
         create_graph(df, pair)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--graph', action='store_true', default=False)
    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    pairs = ["XRPBTC", "XRPETH", "MANABTC", "PPTBTC", "MTHBTC", "BNBBTC", "BNBETH", "ETHBTC" ]
    #pairs =  [x for x in binance.prices().keys() if 'BTC' in x]

    for pair in pairs:
        #PAIR = "XRPBTC"
        #PAIR = "XRPETH"
        #PAIR = "MANABTC"
        get_details(pair, args)
        print

if __name__ == '__main__':
    main()
