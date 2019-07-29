#pylint: disable=logging-not-lazy,wrong-import-position

"""
Functions to fetch data from binance
"""

import sys
import csv
import os


from concurrent.futures import ThreadPoolExecutor
import pandas
import binance

BASE_DIR = os.getcwd().split("greencandle", 1)[0] + "greencandle"
sys.path.append(BASE_DIR)


from .logger import getLogger

LOGGER = getLogger(__name__)

def get_binance_klines(pair, interval=None):
    """
    Get binance klines data for given trading pair and return as a pandas dataframe

    Args:
        pair: trading pair (eg. XRPBTC)
        interval: Interval of each candlestick (eg. 1m, 3m, 15m, 1d etc)

    Returns:
        pandas dataframe containing klines for given pair
    """

    try:
        raw = binance.klines(pair, interval, limit=50)
    except IndexError:
        LOGGER.critical("Unable to fetch data for " + pair)
        sys.exit(2)

    if not raw:
        LOGGER.critical("Empty data for " + pair)
        sys.exit(2)
    dataframe = pandas.DataFrame.from_dict(raw)
    return dataframe

def get_all_klines(pair, interval=None, start_time=0, no_of_klines=1E1000):
    """
    Get all available data for a trading pair
    We are limited to 500 entries per request, so we will loop over until we have fetched all
    entries and collate them together
    initial start time is 0, as far bask as data is available

    Args:
        pair: trading pair (eg. XRPBTC)
        interval: Interval of each candlestick (eg. 1m, 3m, 15m, 1d etc)
        start_time: epochtime we want to start collecting data (milliseconds)
        no_of_klines: number of klines we want to collect

    Returns:
        list of dicts contiaing klines for given pair
    """

    result = []

    while True:
        current_section = binance.klines(pair, interval, startTime=start_time)
        result += current_section
        if len(result) >= no_of_klines:
            # reached maximum
            print("Reached maximum")
            break

        # Start time becomes 1 more than start time of last entry, +1, so that we don"t duplicate
        # entries
        try:
            start_time = current_section[-1]["openTime"] + 1
        except IndexError:
            print("AMROX ERROR: " + str(len(current_section)))
            break
        if len(current_section) < 500:
            # Break out of while true loop as we have exhausted possible entries
            break

    return result[:no_of_klines] if no_of_klines != float("inf") else result

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
    """
    keys = data[0].keys()
    keys = ["closeTime", "low", "high", "open", "close", "volume",
            "openTime", "numTrades", "quoteVolume"]
    with open("{0}.csv".format(pair), "w") as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(reversed(data))

def get_dataframe(pair, interval):
    """
    Extract and return ohlc (open, high, low close) data
    for single pair from available data

    Args:
        pair: trading pair (eg. XRPBTC)
        interval: Interval of each candlestick (eg. 1m, 3m, 15m, 1d etc)

    Returns:
        A truple containing full pandas dataframe and a tuple of float values
    """
    dataframe = get_binance_klines(pair, interval=interval)
    return dataframe

def get_dataframes(pairs, interval=None):
    """
    Get details from binance API

    Args:
        pairs: list of pairss
        interval: Interval used for candlesticks (eg. 1m, 3m, 15m, 1d etc)

    Returns:
        #TODO: fix order of return value, which is opposite of above function
        A truple containing full pandas dataframes and a tuple of float values for all pairs
    """

    pool = ThreadPoolExecutor(max_workers=50)
    dataframe = {}
    results = {}
    for pair in pairs:
        event = {}
        event["symbol"] = pair
        event["data"] = {}
        results[pair] = pool.submit(get_dataframe, pair=pair, interval=interval)

    # extract results
    for key, value in results.items():
        dataframe[key] = value.result()
    pool.shutdown(wait=True)
    return dataframe
