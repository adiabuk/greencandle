#!/usr/bin/env python

"""
Get Supertrend values and trigger points for traing pair
"""

from __future__ import print_function
import os
import json
import csv
import time
import pickle
import pandas
import binance
from indicator import SuperTrend
from morris import KnuthMorrisPratt

HOME_DIR = os.path.expanduser('~')
CONFIG = json.load(open(HOME_DIR + '/.binance'))
API_KEY = CONFIG['api_key']
API_SECRET = CONFIG['api_secret']

def get_binance_dataframe(pair, interval):
    """
    Get pandas dataframe from binance data
    """
    raw = binance.klines(pair, interval)
    dataframe = pandas.DataFrame(raw, columns=['openTime', 'open', 'high', 'low',
                                               'close', 'volume'])
    return dataframe

def get_supertrend(pair="XRPETH"):
    """ get the super trend values """
    dataframe = get_binance_dataframe(pair, "3m")
    columns = ["date", "Open", "High", "Low", "Close", "Volume"]  # rename columns
    for index, item in enumerate(columns):
        dataframe.columns.values[index] = item

    pickle.dump(dataframe, open('/tmp/df', 'wb'))
    mine = dataframe.apply(pandas.to_numeric)
    supertrend = SuperTrend(mine, 10, 3)
    df_list = supertrend['STX_10_3'].tolist()
    return df_list[-10:]

def find_pattern(result, pattern):
    """
    Find Buy/Sell pattern in supertrend results
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
    while True:
        print("Fetching, ", time.time())
        fetch_loop()

def fetch_loop():
    """
    Loop over available trading pairs and find buy/sell triggers
    """
    #pairs = [x for x in binance.prices().keys() if 'BTC' in x or 'ETH' in x]
    #pairs = ["XRPBTC", "XRPETH", "MANABTC", "PPTBTC", "MTHBTC", "BNBBTC", "BNBETH", "ETHBTC"]
    pairs = ["XZCETH"]
    for pair in pairs:
        print("Looping up pair:", pair)
        results = get_supertrend(pair)
        if 7 in [s for s in KnuthMorrisPratt(results, ["down", "up", "up"])]:
            action = "BUY"
        elif 8 in [s for s in KnuthMorrisPratt(results, ["up", "down"])]:
            action = "SELL"
        else:
            action = "HOLD"
        if action == "BUY" or action == "SELL" or action == "HOLD":
            output = (str(pair), str(results), str(action),
                      str(time.time()), str(binance.prices()[pair]))
            print(output)
            append_to_csv(output)
if __name__ == "__main__":
    main()
