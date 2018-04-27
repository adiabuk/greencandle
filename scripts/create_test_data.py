#!/usr/bin/env python
#pylint: disable=wrong-import-position

"""
Download historic data to be used for testing purposes
Save as a pandas dataframe in a pickle file

"""

import os
import sys
import pickle
import pandas

BASE_DIR = os.getcwd().split("greencandle", 1)[0] + "greencandle"
sys.path.append(BASE_DIR)

from lib.binance_common import get_all_klines
from lib.config import get_config

def main():
    """ Main function """

    klines_multiplier = {"15m": 1, "5m": 3, "3m": 5, "1m": 15}
    pairs = get_config("test")["serial_pairs"].split()
    intervals = get_config("test")["serial_intervals"].split()
    start_time = get_config("test")["start_time"].split()
    start_time = sys.argv[1]
    no_of_klines = int(get_config("test")["no_of_klines"].split()[0])
    for pair in pairs:
        for interval in intervals:
            no_of_klines *= int(klines_multiplier[interval])

            filename = BASE_DIR + "/test_data/{0}/{1}_{2}.p".format(sys.argv[2], pair, interval)
            if os.path.exists(filename):
                continue

            current = pandas.DataFrame.from_dict(get_all_klines(pair=pair, interval=interval,
                                                                start_time=start_time,
                                                                no_of_klines=no_of_klines))
            pickle.dump(current, open(filename, "wb"))


if __name__ == "__main__":
    main()
