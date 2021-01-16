#!/usr/bin/env python
#pylint: disable=wrong-import-position,no-member

"""
Check pairs in config are still current
"""
import sys
import time
import datetime
from greencandle.lib import config
config.create_config()
from greencandle.lib.binance_common import get_dataframes


def main():
    """ Main Function """
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("Check if data is downloadable for pair")
        sys.exit(0)

    now = datetime.datetime.now()
    bad_pairs = []
    for pair in config.main.pairs.split():
        try:
            dataframe = get_dataframes([pair], '4h', 1)[pair]
        except:
            print(pair)
            print('no data')
        date = time.gmtime(int(dataframe.iloc[-1]['openTime']/1000))
        if date.tm_year != now.year and date.tm_mon !=now.month:
            print(pair)
            print('no_data')
            bad_pairs.append(pair)
    if bad_pairs:
        sys.exit(1)
