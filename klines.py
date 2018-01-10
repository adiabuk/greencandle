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
class Events(dict):
        def __init__(self, data):
            self.data = data

        def print_text(self):
           red = "\033[31m"
           white = "\033[0m"
           for key, value in self.items():
            if not "direction" in value:
                #no_change.append(value["symbol"])
                continue
            try:
                print("Symbol:", value['symbol'])
                print("URL:", value["URL"])
                print("direction:", value["direction"])
                print("event:", red, value["event"],white)
                print("time:", value["time"])
                for key2, value2 in value["data"].items():
                    print(key2, value2)
            except KeyError:
                print("KEYERROR", value)
                continue
            print("\n")
        #for item in no_change:
        #  print("No Change in", item)


        def get_json():
            return json.dumps(self)

        def get_data(self, pairs):
            for dat in self.data:
                print(pairs)
                for pair in pairs:
                    self.set_data(pair, dat)
                print(self)
                return self

        def set_data(self, pair, dat):
            #print("top of set", pair)
            trends = { "HAMMER": {100:"bullish"},
                       "INVERTEDHAMMER": {100: "bearish"},
                       "ENGULFING": {-100:"bearish", 100:"bullish"},
                       "DOJI": {100: "unknown"} }
            x={}
            for check in trends.keys():
                j = getattr(talib, "CDL" + check)(*dat).tolist()[-10:]
                x.update({check: j})

            for check in trends.keys():
                a={}
                #values = getattr(talib, "CDL" + check)(*data)[-10:]
                #value d= talib.CDLINVERTEDHAMMER(*ohlc)[-10:]
                values = x[check]
                try:
                    #result = trends[check][values.tolist()[-1]]
                    result = trends[check][x[check][-1]]
                    if not "data" in a:
                        a['data'] = {}
                    a["data"]= x #values.tolist()  # convert from array to list
                    a["URL"] = "https://uk.tradingview.com/symbols/{0}/".format(pair)
                    a["time"] = calendar.timegm(time.gmtime())
                    a["symbol"] = pair
                    a["direction"] = result
                    a["event"] = check
                except KeyError as ke:
                    continue
                #print("xxx", a)
                self[id(a)] = a

def get_details(pairs, args):
    """ Get details from binance API """
    ohlcs=[]
    for pair in pairs:
        event = {}
        event["symbol"] = pair
        event['data'] = {}
        raw = binance.klines(pair, "1m")
        epoch = calendar.timegm(time.gmtime())
        dataframe = pandas.DataFrame.from_dict(raw)

        ohlc = (make_float(dataframe.open),
                make_float(dataframe.high),
                make_float(dataframe.low),
                make_float(dataframe.close))
        if args.graph:
            create_graph(dataframe, pair)
        ohlcs.append(ohlc)
    return ohlcs

def main():
    """ main function """
    red = "\033[31m"
    white = "\033[0m"
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--graph', action='store_true', default=False)
    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    data = gen_dict(args)

    no_change=[]

def gen_dict(args):
    pairs = ["XRPBTC", "XRPETH", "MANABTC", "PPTBTC", "MTHBTC", "BNBBTC", "BNBETH", "ETHBTC"]
    #pairs =  [x for x in binance.prices().keys() if 'BTC' in x]
    agg_data = {}
    #agg_data["stories"] = {}
    #agg_data["events"] = {}
    #agg_data["stories"]["time"] = calendar.timegm(time.gmtime())
    #agg_data["stories"]["events"] = []
    #for pair in pairs:

    event_data = get_details(pairs, args)
    events = Events(event_data)
    data = events.get_data(pairs)
    events.print_text()
    #print(data)

        #agg_data["stories"]["events"].append(data["time"])
        #agg_data["events"][data["time"]] = data
    agg_data.update(data)
    return agg_data


if __name__ == '__main__':
    main()
