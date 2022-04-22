#!/usr/bin/env python
#pylint: disable=broad-except
"""
Iterate through pickle data files and get date of first candle close
"""
import time
import gzip
import pickle
import glob
from greencandle.lib.common import arg_decorator

@arg_decorator
def main():
    """
    Print pair and date of first candle close for each pickle
    data file in the current directory in gzip format

    Usage: get_pickle_data
    """
    for filename in glob.glob('*.gz'):

        with gzip.open(filename, 'rb') as handle:
            try:
                dframe = pickle.load(handle)
                date = time.strftime("%Y-%m-%d", time.gmtime(int(dframe.iloc[0].closeTime)/1000))
            except Exception:
                print("skipping {}".format(filename))
            print(filename, date)

if __name__ == '__main__':
    main()
