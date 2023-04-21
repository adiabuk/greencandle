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
    for item in redis.conn.scan_iter("*:12h"):
        pair_set.add(item.decode().split(":")[0])
    pairs = list(pair_set)
    items = defaultdict(dict)
    res = defaultdict(dict)
    last_res = defaultdict(dict)
    agg_res = defaultdict(dict)
    intervals = ['1m', '5m', '1h', '4h', '12h']
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

    # Collect timeframes (milliepochs) for each pair/interval
    for pair in pairs:
        for interval in intervals:
            try:
                items[interval][pair] = redis.get_items(pair=pair, interval=interval)
            except:
                continue

    # Collect data for each pair/interval
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

    # stochf k,d maxed out
    if key == 'stoch_flat':
        data.append(['pair', 'interval', 'avg'])
        for pair in pairs:
            for interval in intervals:
                try:
                    if round(sum(res[interval][pair]['STOCHRSI_8'])/2) >= 100 and \
                            round(sum(last_res[interval][pair]['STOCHRSI_8'])/2) >= 100:
                        data.append([pair, interval, sum(res[interval][pair]['STOCHRSI_8'])/2])

                    elif round(sum(res[interval][pair]['STOCHRSI_8'])/2) <= 0 and \
                            round(sum(last_res[interval][pair]['STOCHRSI_8'])/2) <= 0:
                        data.append([pair, interval,
                                     '{:.2f}'.format(sum(res[interval][pair]['STOCHRSI_8'])/2)])
                except:
                    continue

    # volume
    elif key == 'volume':
        data.append(['pair', 'interval', 'volume'])
        for pair in pairs:
            for interval in intervals:
                try:
                    data.append([pair, interval, res[interval][pair]['ohlc']['volume']])
                except:
                    continue

    # percent between upper and lower bb
    elif key == 'bb_size':
        data.append(['pair', 'interval', 'bb_size'])
        for pair in pairs:
            for interval in intervals:
                try:
                    bb_diff = abs(perc_diff(res[interval][pair]['upper_12'],
                                            res[interval][pair]['lower_12']))

                    data.append([pair, interval, '{:.2f}'.format(bb_diff)])
                except:
                    continue

    # rapid change in bbperc value
    elif key == 'bbperc_diff':
        data.append(['pair', 'interval', 'from', 'to', 'diff'])
        for pair in pairs:
            for interval in intervals:
                try:
                    bb_from = last_res[interval][pair]['bbperc_200']
                    bb_to = res[interval][pair]['bbperc_200']
                    diff = abs(bb_from - bb_to)
                    data.append([pair, interval, '{:.2f}'.format(bb_from), '{:.2f}'.format(bb_to),
                                 '{:.2f}'.format(diff)])
                except:
                    continue

    # change in candle size
    elif key == 'size':
        data.append(['pair', 'interval', 'key'])
        for pair in pairs:
            for interval in intervals:
                try:
                    max_diff = max(abs(perc_diff(res[interval][pair]['ohlc']['high'],
                                                 last_res[interval][pair]['ohlc']['low'])),
                                   abs(perc_diff(res[interval][pair]['ohlc']['low'],
                                                 last_res[interval][pair]['ohlc']['high'])))
                    agg_res[interval][pair] = '{:.2f}'.format(max_diff)
                    data.append([pair, interval, agg_res[interval][pair]])
                except:
                    continue

    # distance between current price and edge of upper/lower bollinger bands
    elif key == 'distance':
        data.append(['pair', 'direction', 'interval', 'distance'])
        for pair in pairs:
            for interval in intervals:
                try:
                    if float(res[interval][pair]['ohlc']['close']) > \
                            float(res[interval][pair]['upper_12']):

                        distance_diff = perc_diff(res[interval][pair]['ohlc']['close'],
                                                  res[interval][pair]['upper_12'])

                    elif float(res[interval][pair]['ohlc']['close']) < \
                            float(res[interval][pair]['lower_12']):
                        distance_diff = abs(perc_diff(res[interval][pair]['ohlc']['close'],
                                                      res[interval][pair]['lower_12']))

                    data.append([pair, "lower", interval, '{:.2f}'.format(distance_diff)])

                except:
                    continue

    # indicator data
    else:
        data.append(['pair', 'interval', indicator])
        for pair in pairs:
            for interval in intervals:
                try:
                    data.append([pair, interval, res[interval][pair][indicator]])

                except:
                    continue

    # save as csv
    timestr = time.strftime("%Y%m%d-%H%M%S")
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
