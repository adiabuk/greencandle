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
import pandas
import binance
from lib.binance_common import get_binance_klines
from lib.graph import create_graph
from lib.morris import KnuthMorrisPratt
from indicator import SuperTrend, RSI
import order

def make_float(arr):
    """Convert dataframe array into float array"""
    return numpy.array([float(x) for x in arr.values])

class Events(dict):
    """ Represent events created from data & indicators """
    def __init__(self, pairs):
        self.pairs = pairs
        self.data = self.get_details()
        super(Events, self).__init__()

    def get_details(self, graph=False, interval="1m"):
        """ Get details from binance API """
        ohlcs = []
        for pair in self.pairs:
            event = {}
            event["symbol"] = pair
            event['data'] = {}

            self.dataframe = get_binance_klines(pair, interval=interval)
            ohlc = (make_float(self.dataframe.open),
                    make_float(self.dataframe.high),
                    make_float(self.dataframe.low),
                    make_float(self.dataframe.close))

            if graph:
                create_graph(self.ataframe, pair)
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
                if value["direction"] != "HOLD":
                    print("direction:", red, value["direction"], white)
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
        for dat in self.data:
            for pair in self.pairs:
                self.get_indicators(pair, dat)
                self.get_supertrend(pair)
                self.get_rsi(pair)
            return self

    def get_rsi(self, pair="PPTBTC"):
        """ get RSI oscillator values """
        dataframe = self.renamed_dataframe_columns()
        scheme = {}
        mine = dataframe.apply(pandas.to_numeric)
        rsi = RSI(mine)
        df_list = rsi['RSI_21'].tolist()
        df_list = ["%.1f" % float(x) for x in df_list]
        scheme["data"] = {"RSI": df_list[-10:]}
        scheme["url"] = self.get_url(pair)
        scheme["time"] = calendar.timegm(time.gmtime())
        scheme["symbol"] = pair
        if float(df_list[-1]) > 70:
            direction = "overbought"
        elif float(df_list[-1]) < 30:
            direction = "oversold"
        else:
            direction = "none"
        scheme["direction"] = direction
        scheme["event"] = "RSI"
        self[id(scheme)] = scheme


    def renamed_dataframe_columns(self):
        """Return dataframe with ordered/renamed coulumns"""
        dataframe = pandas.DataFrame(self.dataframe, columns=['openTime', 'open', 'high',
                                                              'low', 'close', 'volume'])
        columns = ["date", "Open", "High", "Low", "Close", "Volume"]  # rename columns
        for index, item in enumerate(columns):
            dataframe.columns.values[index] = item
        return dataframe



    def get_supertrend(self, pair="XRPETH"):
        """ get the super trend values """
        scheme = {}

        dataframe = pandas.DataFrame(self.dataframe, columns=['openTime', 'open', 'high',
                                                              'low', 'close', 'volume'])
        columns = ["date", "Open", "High", "Low", "Close", "Volume"]  # rename columns
        for index, item in enumerate(columns):
            dataframe.columns.values[index] = item

        mine = dataframe.apply(pandas.to_numeric)
        supertrend = SuperTrend(mine, 10, 3)
        df_list = supertrend['STX_10_3'].tolist()
        scheme["data"] = {"data": {"SUPERTREND": df_list[-10:]}}
        scheme["url"] = self.get_url(pair)
        scheme["time"] = calendar.timegm(time.gmtime())
        scheme["symbol"] = pair
        scheme["direction"] = self.get_supertrend_direction(pair, df_list)
        scheme["event"] = "Supertrend"
        self[id(scheme)] = scheme

    @staticmethod
    def get_url(pair):
        """return graph URL for given pair"""
        return "https://uk.tradingview.com/symbols/{0}/".format(pair)

    @staticmethod
    def get_supertrend_direction(pair, supertrend):
        """Get new direction of supertrend from pattern"""
        if 7 in [s for s in KnuthMorrisPratt(supertrend, ["down", "up", "up"])]:
            action = "BUY"
            price = order.get_buy_price(pair)
        elif 8 in [s for s in KnuthMorrisPratt(supertrend, ["up", "down"])]:
            action = "SELL"
            price = order.get_sell_price(pair)
        elif 0 in [s for s in KnuthMorrisPratt(supertrend, ["nan", "nan", "nan", "nan"])]:
            action = "UNKNOWN"
            price = "irreverent"
        else:
            action = "HOLD"
            price = binance.prices()[pair]
        #x = (str(pair), str(supertrend), str(action),
        #     str(time.time()), str(price))
        return action

    def get_indicators(self, pair, dat):
        """ Cross Reference data against trend indicators """
        #print("top of set", pair)
        trends = {"HAMMER": {100: "bullish", 0:"HOLD"},
                  "INVERTEDHAMMER": {100: "bearish", 0:"HOLD"},
                  "ENGULFING": {-100:"bearish", 100:"bullish", 0:"HOLD"},
                  "DOJI": {100: "unknown", 0:"HOLD"}}
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
                scheme["url"] = self.get_url(pair)
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
    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    pairs = ["XRPBTC", "XRPETH", "MANABTC", "PPTBTC", "MTHBTC", "BNBBTC", "BNBETH", "ETHBTC"]
    #pairs =  [x for x in binance.prices().keys() if 'BTC' in x]
    agg_data = {}
    if args.pair:
        pairs = [args.pair]
        print(args.pair)
    #event_data = get_details(pairs, print_data=False, graph=False)
    events = Events(pairs)
    data = events.get_data()
    if args.json:
        print(json.dumps(events, indent=4))
    else:
        events.print_text()

    agg_data.update(data)
    return agg_data

if __name__ == '__main__':
    main()
