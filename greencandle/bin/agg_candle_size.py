#!/usr/bin/env python
#pylint: disable=no-member,bare-except,too-many-locals,too-many-branches,too-many-statements,no-else-return
"""
get data for all timeframes and pairs
output data to csv files
"""

import json
import sys
import csv
import time
import os
import errno
from collections import defaultdict
from greencandle.lib import config
from greencandle.lib.common import perc_diff, arg_decorator
from greencandle.lib.redis_conn import Redis

def get_bb_size(pair, interval, res):
    """
    percent between upper and lower bb
    """
    try:
        bb_diff = abs(perc_diff(res[interval][pair]['upper_12'],
                                res[interval][pair]['lower_12']))
        bb_diff = '{:.2f}'.format(bb_diff)
    except KeyError:
        bb_diff = ''

    return bb_diff

def symlink_force(target, link_name):
    """
    Create symlink
    If exists, delete and recreate
    """
    try:
        os.symlink(target, link_name)
    except OSError as err:
        if err.errno == errno.EEXIST:
            os.remove(link_name)
            os.symlink(target, link_name)
        else:
            raise err

def average(lst):
    """
    Get average from list of values
    """
    return sum(lst) / len(lst)


@arg_decorator
def main():
    """
    Get min/max/avg candle size for given number of candles
    output data to csv files
    """
    redis = Redis()
    config.create_config()
    pair_set = set()
    for item in redis.conn.scan_iter("*:12h"):
        pair_set.add(item.decode().split(":")[0])
    pairs = list(pair_set)
    items = defaultdict(dict)
    res = defaultdict(dict)
    intervals = ['1m', '5m', '1h', '4h', '12h']
    data = []
    key = 'candle_size'
    samples = sys.argv[1]
    print(samples)


    # Collect timeframes (milliepochs) for each pair/interval
    for pair in pairs:
        for interval in intervals:
            try:
                items[interval][pair] = redis.get_items(pair=pair,
                                                        interval=interval)[-int(samples):-1]
            except:
                continue
    # Collect data for each pair/interval
    for pair in pairs:
        for interval in intervals:
            res[interval][pair] = {}

            for item in items[interval][pair]:
                try:
                    res[interval][pair][item] = json.loads(redis.get_item('{}:{}'.format(pair,
                                                                                         interval),
                                                                          item).decode())
                except:
                    continue
    data.append(["pair", "interval", "max", "min", "avg"])
    for interval in intervals:
        for pair in pairs:
            diffs = []
            for item in items[interval][pair]:
                try:
                    diffs.append(perc_diff(res[interval][pair][item]['ohlc']['low'],
                                           res[interval][pair][item]['ohlc']['high']))
                except:
                    pass
            if diffs:
                data.append([pair, interval, round(max(diffs), 2),
                             round(min(diffs), 2), round(average(diffs), 2)])

    timestr = time.strftime("%Y%m%d-%H%M%S")
    # save as csv
    with open('/data/aggregate/{}_{}.csv'.format(key, timestr),
              'w', encoding='UTF8', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerows(data)
    # save as tsv
    with open('/data/aggregate/{}_{}.tsv'.format(key, timestr),
              'w', encoding='UTF8', newline='') as handle:
        writer = csv.writer(handle, delimiter='\t')
        writer.writerows(data)

    # create/overwrite symlink to most recent file
    os.chdir('/data/aggregate')
    symlink_force('../{}_{}.tsv'.format(key, timestr), 'current/{}.tsv'.format(key))
    symlink_force('../{}_{}.csv'.format(key, timestr), 'current/{}.csv'.format(key))
    print('DONE')

if __name__ == '__main__':
    main()
