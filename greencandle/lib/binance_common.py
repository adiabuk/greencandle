#pylint: disable=logging-not-lazy,wrong-import-position,no-member

"""
Functions to fetch data from binance
"""

import sys
import csv
import os
import pickle
import time
import datetime
from concurrent.futures import ThreadPoolExecutor
import pandas
import binance


from . import config
from .logger import get_logger

LOGGER = get_logger(__name__)

def get_current_price(pair):
    """Get current price from binance"""
    prices = binance.prices()
    return prices[pair]

def get_binance_klines(pair, interval=None, limit=50):
    """
    Get binance klines data for given trading pair and return as a pandas dataframe

    Args:
        pair: trading pair (eg. XRPBTC)
        interval: Interval of each candlestick (eg. 1m, 3m, 15m, 1d etc)

    Returns:
        pandas dataframe containing klines for given pair
    """

    try:
        raw = binance.klines(pair, interval, limit=limit)
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
            break
        if len(current_section) < 500:
            # Break out of while true loop as we have exhausted possible entries
            break

    return result[:no_of_klines] if no_of_klines != float("inf") else result

def get_data(startdate, intervals, pairs, days, outputdir, extra):
    """Calculate which data to fetch given args and fetch into outputdir"""

    given_date = datetime.datetime.strptime(startdate, '%Y-%m-%d')
    given_start_epoch = time.mktime(given_date.timetuple())

    daily_minutes = 1440  # number of minutes in a day

    # For testing we use 50 klines buffer to calculate trends/averages etc.
    # so we need to add 50 more klines to the end (total_klines) so that we
    #still end up with the exact number of lines for the days specified
    number_of_extra_klines = extra

    klines_multiplier = {"1d": 720,
                         "4h": 240,
                         "2h": 120,
                         "1h": 60,
                         "30m": 30,
                         "15m": 15,
                         "5m": 5,
                         "3m": 3,
                         "1m": 1}

    intervals = intervals if intervals else klines_multiplier.keys()
    for pair in pairs:
        for interval in intervals:
            if not os.path.isdir(outputdir):
                sys.exit("Invalid output directory: {0}".format(outputdir))
            filename = "{0}/{1}_{2}.p".format(outputdir.rstrip('/'), pair, interval)
            print("Using filename:", filename)
            if os.path.exists(filename) or os.path.exists(filename + '.gz'):
                continue


            # calculate start_time, and number of klines we need for interval
            ###################################
            seconds_per_kline = klines_multiplier[interval] * 60

            # number of seconds ealier we need to start
            additional_seconds = seconds_per_kline * number_of_extra_klines
            actual_start_epoch = given_start_epoch - additional_seconds
            klines_in_a_day = daily_minutes * (1/klines_multiplier[interval])
            total_klines = int(klines_in_a_day) * int(days) + number_of_extra_klines
            start_mepoch = int(actual_start_epoch * 1000)
            ###################################

            print("Getting {0} klines for {1} {2} - {3} days".format(total_klines,
                                                                     pair, interval, days))
            current = pandas.DataFrame.from_dict(get_all_klines(pair=pair, interval=interval,
                                                                start_time=start_mepoch,
                                                                no_of_klines=total_klines))
            with open(filename, "wb") as output:
                pickle.dump(current, output)

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

def get_dataframe(pair, interval, no_of_klines):
    """
    Extract and return ohlc (open, high, low close) data
    for single pair from available data

    Args:
        pair: trading pair (eg. XRPBTC)
        interval: Interval of each candlestick (eg. 1m, 3m, 15m, 1d etc)

    Returns:
        A truple containing full pandas dataframe and a tuple of float values
    """
    dataframe = get_binance_klines(pair, interval=interval, limit=int(no_of_klines))
    return dataframe

def get_dataframes(pairs, interval=None, no_of_klines=None):
    """
    Get details from binance API

    Args:
        pairs: list of pairss
        interval: Interval used for candlesticks (eg. 1m, 3m, 15m, 1d etc)

    Returns:
        #TODO: fix order of return value, which is opposite of above function
        A truple containing full pandas dataframes and a tuple of float values for all pairs
    """
    if not no_of_klines:
        no_of_klines = config.main.no_of_klines

    pool = ThreadPoolExecutor(max_workers=50)
    dataframe = {}
    results = {}
    for pair in pairs:
        event = {}
        event["symbol"] = pair
        event["data"] = {}
        results[pair] = pool.submit(get_dataframe, pair=pair, interval=interval,
                                    no_of_klines=no_of_klines)

    # extract results
    for key, value in results.items():
        dataframe[key] = value.result()
    pool.shutdown(wait=True)
    return dataframe
