#!/usr/bin/env python

"""
Get Supertrend values for traing pair
"""

from __future__ import print_function
import os
import json
import pickle
import pandas
import binance
from indicator import SuperTrend

HOME_DIR = os.path.expanduser('~')
CONFIG = json.load(open(HOME_DIR + '/.binance'))
API_KEY = CONFIG['api_key']
API_SECRET = CONFIG['api_secret']


def get_binance_dataframe(pair, interval):
    raw = binance.klines(pair, interval)
    dataframe = pandas.DataFrame(raw, columns=['openTime', 'open', 'high', 'low',
                                               'close', 'volume'])
    return dataframe



def get_supertrend(pair="XRPETH"):
    """ get the super trend values """
    dataframe = get_binance_dataframe("XRPETH", "1m")
    columns = ["date", "Open", "High", "Low", "Close", "Volume"]  # rename columns
    for index, item in enumerate(columns):
        dataframe.columns.values[index] = item

    pickle.dump(dataframe, open('/tmp/df', 'wb'))
    mine = dataframe.apply(pandas.to_numeric)
    supertrend = SuperTrend(mine, 10, 3)
    df_list = supertrend['STX_10_3'].tolist()
    return df_list[-10:]

def main():
    """ Main function """
    print(get_supertrend("XRPETH"))
if __name__ == "__main__":
    main()
