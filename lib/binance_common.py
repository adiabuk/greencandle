import sys
import pandas
import binance

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
