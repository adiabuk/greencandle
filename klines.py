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
        super(Events, self).__init__()

    def print_text(self):
        """
        Print text output to stdout
        """
        red = "\033[31m"
        white = "\033[0m"
        if not self.values:
            print("ERROR")
        for value in self.values():
            if not "direction" in value:
            #no_change.append(value["symbol"])
                continue
            try:
                print("Symbol:", value['symbol'])
                print("URL:", value["URL"])
                print("direction:", value["direction"])
                print("event:", red, value["event"], white)
                print("time:", value["time"])
                for key2, value2 in value["data"].items():
                    print(key2, value2)
            except KeyError:
                print("KEYERROR", value)
                continue
            print("\n")

    def get_json(self):
        """return serialized JSON of dict """
        sys.stderr.write(json.dumps(self))
        return json.dumps(self)

    def get_data(self, pairs):
        """Iterate through data and trading pairs to extract data"""

        for dat in self.data:
            for pair in pairs:
                self.set_data(pair, dat)
            return self

    def set_data(self, pair, dat):
        #print("top of set", pair)
        trends = {"HAMMER": {100: "bullish"},
                  "INVERTEDHAMMER": {100: "bearish"},
                  "ENGULFING": {-100:"bearish", 100:"bullish"},
                  "DOJI": {100: "unknown"}}
        x = {}
        for check in trends.keys():
            j = getattr(talib, "CDL" + check)(*dat).tolist()[-10:]
            x.update({check: j})

        for check in trends.keys():
            a={}
            values = x[check]
            try:
                result = trends[check][x[check][-1]]
                if not "data" in a:
                    a['data'] = {}
                a["data"]= x   # convert from array to list
                a["URL"] = "https://uk.tradingview.com/symbols/{0}/".format(pair)
                a["time"] = calendar.timegm(time.gmtime())
                a["symbol"] = pair
                a["direction"] = result
                a["event"] = check
            except KeyError as ke:
                continue
            self[id(a)] = a

def get_details(pairs, args):
    """ Get details from binance API """
    ohlcs=[]
    for pair in pairs:
        event = {}
        event["symbol"] = pair
        event['data'] = {}
        raw = binance.klines(pair, "1m")
        if not raw:
            sys.stderr.write("Unable to extract data")
            sys.exit(2)
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

def gen_dict(args):
    pairs = ["XRPBTC", "XRPETH", "MANABTC", "PPTBTC", "MTHBTC", "BNBBTC", "BNBETH", "ETHBTC"]
    #pairs =  [x for x in binance.prices().keys() if 'BTC' in x]
    agg_data = {}

    event_data = get_details(pairs, args)
    events = Events(event_data)
    data = events.get_data(pairs)
    events.print_text()
    agg_data.update(data)
    return agg_data


if __name__ == '__main__':
    main()
