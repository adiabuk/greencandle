#!/usr/bin/env python
#pylint: disable=no-member, bare-except,too-many-locals, too-many-branches, too-many-statements
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

@arg_decorator
def main():
    """
    get data for all timeframes and pairs
    output data to csv files
    """
    redis = Redis()
    config.create_config()
    key = sys.argv[1]
    pair_set = set()
    for item in redis.conn.scan_iter("*:1m"):
        pair_set.add(item.decode().split(":")[0])
    pairs = list(pair_set)
    items = defaultdict(dict)
    res = defaultdict(dict)
    last_res = defaultdict(dict)
    agg_res = defaultdict(dict)
    intervals = ['1m', '5m', '1h', '4h']
    data = []
    if key == 'keys':
        items_1h = redis.get_items('BTCUSDT', '1h')
        keys = json.loads(redis.get_item('BTCUSDT:1h', items_1h[-1]).decode()).keys()
        print(keys)
        sys.exit()
    elif key == 'distance':
        indicator = 'upper_12'
    else:
        indicator = key

    for pair in pairs:
        for interval in intervals:
            try:
                items[interval][pair] = redis.get_items(pair=pair, interval=interval)
            except:
                continue

    for pair in pairs:
        for interval in intervals:
            try:
                res[interval][pair] = json.loads(redis.get_item('{}:{}'.format(pair, interval),
                                                                items[interval][pair][-1]).decode())
                last_res[interval][pair] = json.loads(redis.get_item('{}:{}'.format(pair, interval),
                                                                     items[interval][pair][-2])
                                                      .decode())

            except:
                continue

    if key == 'stoch_flat':
        data.append(['pair', 'interval', 'avg'])
        for pair in pairs:
            for interval in intervals:
                if round(sum(res[interval][pair]['STOCHRSI_8'])/2) >= 100 and \
                        round(sum(last_res[interval][pair]['STOCHRSI_8'])/2) >= 100:
                    data.append([pair, interval, sum(res[interval][pair]['STOCHRSI_8'])/2])

                elif round(sum(res[interval][pair]['STOCHRSI_8'])/2) <= 0 and \
                        round(sum(last_res[interval][pair]['STOCHRSI_8'])/2) <= 0:
                    data.append([pair, interval, sum(res[interval][pair]['STOCHRSI_8'])/2])

    elif key == 'bbperc_diff':
        data.append(['pair', 'interval', 'diff', 'from', 'to'])
        for pair in pairs:
            for interval in intervals:
                try:
                    bb_from = last_res[interval][pair]['bbperc_200']
                    bb_to = res[interval][pair]['bbperc_200']
                    diff = perc_diff(bb_from, bb_to)
                except TypeError:
                    continue
                data.append([pair, interval, diff, bb_from, bb_to])

    elif key == 'size':
        data.append(['pair', '1m', '5m', '1h', '4h'])
        for pair in pairs:
            for interval in intervals:
                max_diff = max(abs(perc_diff(res[interval][pair]['ohlc']['high'],
                                             last_res[interval][pair]['ohlc']['low'])),
                               abs(perc_diff(res[interval][pair]['ohlc']['low'],
                                             last_res[interval][pair]['ohlc']['high'])))
                agg_res[interval][pair] = max_diff
            data.append([pair, agg_res['1m'][pair], agg_res['5m'][pair],
                         agg_res['1h'][pair], agg_res['4h'][pair]])

    elif key == 'distance':
        data.append(['pair', 'direction', 'interval', 'distance'])
        for pair in pairs:
            for interval in intervals:
                try:
                    if float(res[interval][pair]['ohlc']['close']) > \
                            float(res[interval][pair]['upper_12']):

                        data.append([pair, "upper", interval,
                                     perc_diff(res[interval][pair]['ohlc']['close'],
                                               res[interval][pair]['upper_12'])])

                    elif float(res[interval][pair]['ohlc']['close']) < \
                            float(res[interval][pair]['lower_12']):

                        data.append([pair, "lower", interval,
                                     perc_diff(res[interval][pair]['ohlc']['close'],
                                               res[interval][pair]['lower_12'])])

                except:
                    pass

    else:
        data.append(['pair', '1m', '5m', '1h', '4h'])
        for pair in pairs:
            try:
                data.append([pair,
                             res['1m'][pair][indicator],
                             res['5m'][pair][indicator],
                             res['1h'][pair][indicator],
                             res['4h'][pair][indicator]])

            except:
                continue

    timestr = time.strftime("%Y%m%d-%H%M%S")
    with open('/data/aggregate/{}_{}.csv'.format(key, timestr),
              'w', encoding='UTF8', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerows(data)

    with open('/data/aggregate/{}_{}.tsv'.format(key, timestr),
              'w', encoding='UTF8', newline='') as handle:
        writer = csv.writer(handle, delimiter='\t')
        writer.writerows(data)

    os.chdir('/data/aggregate')
    symlink_force('../{}_{}.tsv'.format(key, timestr), 'current/{}.tsv'.format(key))
    symlink_force('../{}_{}.csv'.format(key, timestr), 'current/{}.csv'.format(key))
    print('DONE')

if __name__ == '__main__':
    main()
