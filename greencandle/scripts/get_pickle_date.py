#!/usr/bin/env python
"""
Iterate through pickle data files and get date of first candle close
"""
import time
import gzip
import pickle
import glob

def main():
    """
    Print pair and date of first candle close for each pickle
    data file in the current directory in gzip format
    """
    for filename in glob.glob('*.gz'):

        with gzip.open(filename, 'rb') as handle:
            dframe = pickle.load(handle)
            date = time.strftime("%Y-%m-%d", time.gmtime(int(dframe.iloc[0].closeTime)/1000))
            print(filename, date)

if __name__ == '__main__':
    main()
