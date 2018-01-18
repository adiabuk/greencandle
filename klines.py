#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
#pylint: disable=no-member,consider-iterating-dictionary

"""
Get ohlc (Open, High, Low, Close) values from given cryptos
and detect trends using candlestick patterns
"""

from __future__ import print_function
import json
import argparse
import time
import calendar
import numpy
import talib
import argcomplete
from lib.binance_common import get_binance_klines
from lib.graph import create_graph

def make_float(arr):
    """Convert dataframe array into float array"""
    return numpy.array([float(x) for x in arr.values])

class Events(dict):
    """ Represent events created from data & indicators """
    def __init__(self, pairs):

        self.pairs = pairs
        self.data = self.get_details()
        super(Events, self).__init__()

    def get_details(self, print_data=False, graph=False, interval="1m"):
        """ Get details from binance API """
        ohlcs = []
        for pair in self.pairs:
            event = {}
            event["symbol"] = pair
            event['data'] = {}

            dataframe = get_binance_klines(pair, interval=interval)
            if print_data:
                # FIXME: this is in the wrong place
                # print datafram and return
                # Will not print out indicators!
                print(dataframe)
                return {}

            ohlc = (make_float(dataframe.open),
                    make_float(dataframe.high),
                    make_float(dataframe.low),
                    make_float(dataframe.close))

            if graph:
                create_graph(dataframe, pair)
            ohlcs.append(ohlc)
        return ohlcs

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
                print("URL:", value["url"])
                if value["direction"] != "keep":
                    print("direction: {0}{1}{2}".format, red, value["direction"], white)
                else:
                    print("direction:", value["direction"])
                print("event:", red, value["event"], white)
                print("time:", value["time"])
                for key2, value2 in value["data"].items():
                    print(key2, value2)
            except KeyError as key_error:
                print("KEYERROR", value, key_error)
                continue
            print("\n")

    def get_json(self):
        """return serialized JSON of dict """
        return json.dumps(self)

    def get_data(self):
        """Iterate through data and trading pairs to extract data"""
        print("get data method")
        for dat in self.data:
            for pair in self.pairs:
                self.set_data(pair, dat)
            return self

    def set_data(self, pair, dat):
        """ Cross Reference data against trend indicators """
        #print("top of set", pair)
        trends = {"HAMMER": {100: "bullish", 0:"keep"},
                  "INVERTEDHAMMER": {100: "bearish", 0:"keep"},
                  "ENGULFING": {-100:"bearish", 100:"bullish", 0:"keep"},
                  "DOJI": {100: "unknown", 0:"keep"}}
        results = {}
        for check in trends.keys():
            j = getattr(talib, "CDL" + check)(*dat).tolist()[-10:]
            results.update({check: j})

        for check in trends.keys():
            scheme = {}
            try:
                result = trends[check][results[check][-1]]
                if "data" not in scheme:
                    scheme['data'] = {}
                scheme["data"] = results   # convert from array to list
                scheme["url"] = "https://uk.tradingview.com/symbols/{0}/".format(pair)
                scheme["time"] = calendar.timegm(time.gmtime())
                scheme["symbol"] = pair
                scheme["direction"] = result
                scheme["event"] = check
            except KeyError:
                continue
            self[id(scheme)] = scheme


def main():
    """ main function """
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--graph', action='store_true', default=False)
    parser.add_argument('-j', '--json', action='store_true', default=False)
    parser.add_argument('-p', '--pair')
    parser.add_argument('-d', '--print_data', action='store_true', default=False)
    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    gen_dict(args)

def gen_dict(args):
    """ Create dict of data for all pairs """
    pairs = ["XRPBTC", "XRPETH", "MANABTC", "PPTBTC", "MTHBTC", "BNBBTC", "BNBETH", "ETHBTC"]
    #pairs =  [x for x in binance.prices().keys() if 'BTC' in x]
    agg_data = {}
    if args.pair:
        pairs = [args.pair]
        print(args.pair)
    #event_data = get_details(pairs, print_data=False, graph=False)
    events = Events(pairs)
    data = events.get_data()
    #while not data:
    #    sys.stderr.write("ERROR"+ str(pairs)+ "\n")
    #    events = Events(pairs)
    #    data = events.get_data()
    if args.json:
        print(json.dumps(events, indent=4))
    else:
        events.print_text()

    agg_data.update(data)
    return agg_data

if __name__ == '__main__':
    main()
