#!/usr/bin/env python
#pylint: disable=wrong-import-position

"""
Download historic data to be used for testing purposes
Save as a pandas dataframe in a pickle file

"""

import os
import sys
import pickle
import time
import datetime
import pandas

BASE_DIR = os.getcwd().split("greencandle", 1)[0] + "greencandle"
sys.path.append(BASE_DIR)

from ..lib.binance_common import get_all_klines

def main():
    """ Main function """
    if len(sys.argv) <= 2:
        sys.exit("Usage: {0} <time> <days> <pairs>".format(sys.argv[0]))

    start_time = sys.argv[1]
    days = int(sys.argv[2])
    pairs = sys.argv[3:]


    dt = datetime.datetime.strptime(start_time, '%Y-%m-%d')
    given_start_epoch = time.mktime(dt.timetuple())
    number_of_extra_klines = 50
    no_of_klines = 1440  # number of minutes in a day

    klines_multiplier = {"15m": 15,
                         "5m": 5,
                         "3m": 3,
                         "1m": 1}

    for pair in pairs:
        for interval in ['1m', '3m', '5m', '15m']:
            if not os.path.isdir('/tmp/test_data'):
                os.mkdir('/tmp/test_data')
            filename = "/tmp/test_data/{0}_{1}.p".format(pair, interval)
            print("Using filename:", filename)
            if os.path.exists(filename):
                continue

            # For testing we use 50 klines buffer to calculate trends/averages etc.
            # so we need to add 50 more klines by calculating how much time that would be depending
            # on the interval
            ###################################
            seconds_per_kline = klines_multiplier[interval] * 60
            additional_seconds = seconds_per_kline * number_of_extra_klines
            actual_start_epoch = given_start_epoch - additional_seconds
            klines_in_a_day = no_of_klines * (1/klines_multiplier[interval])
            total_klines = int(klines_in_a_day * days)
            start_mepoch = int(actual_start_epoch * 1000)
            ###################################

            print("Getting {0} klines for {1} {2} - {3} days".format(total_klines,
                                                                     pair, interval, days))
            current = pandas.DataFrame.from_dict(get_all_klines(pair=pair, interval=interval,
                                                                start_time=start_mepoch,
                                                                no_of_klines=total_klines))
            pickle.dump(current, open(filename, "wb"))

if __name__ == "__main__":
    main()
