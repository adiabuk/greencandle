#pylint: disable=no-member,too-many-arguments,too-many-locals


"""
Functions to fetch data from binance
"""

import sys
import csv
import os
import pickle
import time
import datetime
from concurrent.futures import ProcessPoolExecutor
import pandas
from greencandle.lib.binance import Binance
from greencandle.lib import config
from greencandle.lib.logger import get_logger
from greencandle.lib.common import epoch2date, TF2MIN

LOGGER = get_logger(__name__)

def get_current_price(pair, prices=None):
    """Get current price from binance"""

    client = Binance()
    prices = prices if prices else client.prices()
    return prices[pair]

def get_binance_klines(pair, interval=None, limit=50):
    """
    Get binance klines data for given trading pair and return as a pandas dataframe

    Args:
        pair: trading pair (eg. XRPBTC)
        interval: Interval of each candl estick (eg. 1m, 3m, 15m, 1d etc)

    Returns:
        pandas dataframe containing klines for given pair
    """

    try:
        client = Binance()
        interval = "1m" if interval.endswith("s") else interval
        raw = client.klines(pair, interval, limit=limit)

    except IndexError:
        LOGGER.critical("Unable to fetch data for %s", pair)
        sys.exit(2)

    if not raw:
        LOGGER.critical("Empty data for %s", pair)
        sys.exit(2)

    non_empty = [x for x in raw if x['numTrades'] != 0]
    dataframe = pandas.DataFrame.from_dict(non_empty)
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
        client = Binance()
        current_section = client.klines(pair, interval, startTime=start_time)
        result += current_section
        if len(result) >= no_of_klines:
            # reached maximum
            LOGGER.debug("Reached maximum number of candles")
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
    try:
        first_candle = result[0]['openTime']/1000
        last_candle = result[-1]['closeTime']/1000
    except IndexError:
        LOGGER.info("No candles for %s", pair)
        return None

    start = epoch2date(first_candle)
    end = epoch2date(last_candle)
    LOGGER.debug("%s Start: %s, End: %s", pair, start, end)

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
        pair = pair.strip()
        for interval in intervals:
            if not os.path.isdir(outputdir):
                sys.exit(f"Invalid output directory: {outputdir}")
            filename = f"{outputdir.rstrip('/')}/{pair}_{interval}.p"
            LOGGER.debug("Using filename: %s", filename)
            if os.path.exists(filename) or os.path.exists(filename + '.gz'):
                LOGGER.debug("File already exists, skipping")
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

            LOGGER.debug("Getting %s klines for %s %s - %s days", total_klines, pair, interval,
                         days)
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
    with open(f"{pair}.csv", "w") as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(reversed(data))

def get_dataframes(pairs, interval=None, no_of_klines=None, max_workers=30):
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

    pool = ProcessPoolExecutor(max_workers=max_workers)
    futures = []

    dataframe = {}
    for pair in pairs:
        futures.append(pool.submit(get_non_empty, pair=pair, interval=interval,
                                   no_of_klines=int(no_of_klines)))

    pool.shutdown(wait=False)
    for item in futures:
        pair, dframe = item.result()
        dataframe[pair] = dframe

    return dataframe

def get_non_empty(pair, interval, no_of_klines):
    """
    Get candles for given pair | interval
    and filter out empty data, ensuring we have enough candles
    specified by no_of_klines
    """
    count = 0
    initial_klines = no_of_klines

    while count <= initial_klines:

        start_time = int(time.time()*1000) - int((int(no_of_klines)) * \
                TF2MIN[interval]*60000)
        klines = get_all_klines(pair, interval=interval, start_time=start_time,
                                no_of_klines=no_of_klines)
        non_empty = [x for x in klines if x['numTrades'] != 0][-no_of_klines:]
        count = len(non_empty)
        no_of_klines += initial_klines
    return pair, pandas.DataFrame(non_empty)
