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
            klines = no_of_klines * int(klines_multiplier[interval]) +50

            filename = BASE_DIR + "/test_data/{0}/{1}_{2}.p".format(sys.argv[2], pair, interval)
            if os.path.exists(filename):
                continue
            adiitional_klines = 50
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
