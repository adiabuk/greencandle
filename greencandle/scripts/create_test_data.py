#!/usr/bin/env python
#pylint: disable=wrong-import-position

"""
Download historic data to be used for testing purposes
Save as a pandas dataframe in a pickle file

"""

import argparse
import os
import sys
import pickle
import time
import datetime
import pandas
import argcomplete

from ..lib import config
config.create_config(test=True)
from ..lib.binance_common import get_all_klines

def main():
    """ Main function """

    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--startdate", required=True)
    parser.add_argument("-d", "--days", required=True)
    parser.add_argument("-o", "--outputdir", required=True)
    parser.add_argument("-p", "--pairs", nargs='+', required=True, default=[])
    parser.add_argument("-i", "--intervals", nargs='+', required=False, default=[])

    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    given_date = datetime.datetime.strptime(args.startdate, '%Y-%m-%d')
    given_start_epoch = time.mktime(given_date.timetuple())

    daily_minutes = 1440  # number of minutes in a day

    # For testing we use 50 klines buffer to calculate trends/averages etc.
    # so we need to add 50 more klines to the end (total_klines) so that we
    #still end up with the exact number of lines for the days specified
    number_of_extra_klines = 50

    klines_multiplier = {"4h": 240,
                         "2h": 120,
                         "1h": 60,
                         "30m": 30,
                         "15m": 15,
                         "5m": 5,
                         "3m": 3,
                         "1m": 1}

    intervals = args.intervals if args.intervals else klines_multiplier.keys()
    for pair in args.pairs:
        for interval in intervals:
            if not os.path.isdir(args.outputdir):
                sys.exit("Invalid output directory: {0}".format(args.outputdir))
            filename = "{0}/{1}_{2}.p".format(args.outputdir.rstrip('/'), pair, interval)
            print("Using filename:", filename)
            if os.path.exists(filename):
                continue


            # calculate start_time, and number of klines we need for interval
            ###################################
            seconds_per_kline = klines_multiplier[interval] * 60

            # number of seconds ealier we need to start
            additional_seconds = seconds_per_kline * number_of_extra_klines
            actual_start_epoch = given_start_epoch - additional_seconds
            klines_in_a_day = daily_minutes * (1/klines_multiplier[interval])
            total_klines = int(klines_in_a_day) * int(args.days) + number_of_extra_klines
            start_mepoch = int(actual_start_epoch * 1000)
            ###################################

            print("Getting {0} klines for {1} {2} - {3} days".format(total_klines,
                                                                     pair, interval, args.days))
            current = pandas.DataFrame.from_dict(get_all_klines(pair=pair, interval=interval,
                                                                start_time=start_mepoch,
                                                                no_of_klines=total_klines))
            pickle.dump(current, open(filename, "wb"))

if __name__ == "__main__":
    main()
