import sys
import pandas
import binance
import csv

def get_binance_klines(pair, interval="1m"):
    """
    get binance klines data for given trading pair and return as a pandas dataframe
    """
    try:
        raw = binance.klines(pair, interval)
    except IndexError:
        sys.stderr.write("Unable to fetch data for " + pair + "\n")
        sys.exit(2)
    if not raw:
        sys.stderr.write("Unable to extract data")
        sys.exit(2)
    dataframe = pandas.DataFrame.from_dict(raw)
    return dataframe

def get_all_klines(symbol, interval=None, start_time=0):
    """
    Get all available data for a trading pair
    We are limited to 500 entries per request, so we will loop over until we have fetched all
    entries
    initial start time is 0, as far bask as data is available
    """

    result = []

    while True:
        current_section = binance.klines(symbol, interval, startTime=start_time)
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
    """

    keys = data[0].keys()
    keys = ["closeTime", "low", "high", "open", "close", "volume",
            "openTime", "numTrades", "quoteVolume"]
    with open('{0}.csv'.format(pair), 'w') as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        dict_writer.writerows(reversed(data))
