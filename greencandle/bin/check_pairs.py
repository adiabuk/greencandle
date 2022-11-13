#!/usr/bin/env python
#pylint: disable=wrong-import-position,no-member,bare-except

"""
Check pairs in config are still current
"""
import time
import datetime
from greencandle.lib.common import arg_decorator
from greencandle.lib import config
config.create_config()
from greencandle.lib.binance_common import get_dataframes

@arg_decorator
def main():
    """
    Check pairs are valid by attempting to download a single candle
    from the exchange - uses pairs defined in config

    Usage: check_pairs
    """
    now = datetime.datetime.now()
    good_pairs = []
    for pair in config.main.pairs.split():
        pair = pair.strip()
        try:
            dataframe = get_dataframes([pair], '4h', 1)[pair]
        except:
            print(pair)
            print('no data')
        date = time.gmtime(int(dataframe.iloc[-1]['openTime']/1000))
        if date.tm_year != now.year and date.tm_mon != now.month:
            print(pair)
            print('no_data')
            good_pairs.append(pair)

    print(good_pairs)
