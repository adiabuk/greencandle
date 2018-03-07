"""
Functions to fetch data from binance
"""

import sys
import pandas
import binance
import csv

from lib.logger import getLogger
logger = getLogger(__name__)

def get_binance_klines(pair, interval=None):
    """
    Get binance klines data for given trading pair and return as a pandas dataframe

    Args:
        pair: trading pair (eg. XRPBTC)
        interval: Interval of each candlestick (eg. 1m, 3m, 15m, 1d etc)

    Returns:
        pandas datafram contiaing klines for given pair
    """

    try:
        raw = binance.klines(pair, interval)
    except IndexError:
        logger.critical("Unable to fetch data for " + pair)
        sys.exit(2)

    if not raw:
        logger.critical("Unable to extract data")
        sys.exit(2)
    dataframe = pandas.DataFrame.from_dict(raw)
    return dataframe

def get_all_klines(pair, interval=None, start_time=0):
    """
    Get all available data for a trading pair
    We are limited to 500 entries per request, so we will loop over until we have fetched all
    entries and collate them together
    initial start time is 0, as far bask as data is available

    Args:
        pair: trading pair (eg. XRPBTC)
        interval: Interval of each candlestick (eg. 1m, 3m, 15m, 1d etc)
        start_time: epochtime we want to start collecting data.

    Returns:
        pandas datafram contiaing klines for given pair
    """

    result = []

    while True:
        current_section = binance.klines(pair, interval, startTime=start_time)
        result += current_section

        # Start time becomes 1 more than start time of last entry, +1, so that we don't duplicate
        # entries
        start_time = current_section[-1]['openTime'] + 1
        if len(current_section) < 500:
            # Break out of while true loop as we have exhausted possible entries
            break

    return result

def to_csv(pair, data):
    """
    Create csv from klines data
    File created in current working directory as <pair>.csv contiaing the following fields:
    closeTime, low, high, open, close, volume,
            openTime, numTrades, quoteVolume
    data order is reversed so that most recent is at the top (descending order)


    Args:
        pair: trading pair (eg. XRPBTC)
        data: pandas dataframe containing klines data

    Returns:
        pandas datafram contiaing klines for given pair
    """


    keys = data[0].keys()
    keys = ["closeTime", "low", "high", "open", "close", "volume",
            "openTime", "numTrades", "quoteVolume"]
    with open('{0}.csv'.format(pair), 'w') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(reversed(data))
