#!/usr/bin/env python
#pylint: disable=wrong-import-position

"""
Download historic data to be used for testing purposes
Save as a pandas dataframe in a pickle file

"""

import os
import sys
import re
import pickle
import pandas

BASE_DIR = os.getcwd().split("greencandle", 1)[0] + "greencandle"
sys.path.append(BASE_DIR)

from ..lib.binance_common import get_all_klines

def main():
    """ Main function """
    if len(sys.argv) <= 2:
        sys.exit("Usage: {0} <mepoch> <pairs>".format(sys.argv[0]))
    no_of_klines = 1440  # number of minutes in a day
    additional_klines = 50
    klines_multiplier = {"15m": 1/15,
                         "5m": 1/5,
                         "3m": 1/3,
                         "1m": 1}
    pairs = sys.argv[2:]
    start_time = sys.argv[1]

    for pair in pairs:
        for interval in ['1m', '3m', '5m', '15m']:
            klines = int(no_of_klines * klines_multiplier[interval]) + additional_klines
            if not os.path.isdir('/tmp/test_data'):
                os.mkdir('/tmp/test_data')
            filename = "/tmp/test_data/{0}_{1}.p".format(pair, interval)
            print("Using filename:", filename)
            if os.path.exists(filename):
                continue
            minutes = [int(s) for s in re.findall(r'(\d+)m', interval)][0]
            milliseconds = minutes * 60000
            real_start_time = int(start_time) - milliseconds
            print("Getting {0} klines for {1} {2}".format(klines, pair, interval))
            current = pandas.DataFrame.from_dict(get_all_klines(pair=pair, interval=interval,
                                                                start_time=real_start_time,
                                                                no_of_klines=klines))
            pickle.dump(current, open(filename, "wb"))

if __name__ == "__main__":
    main()
