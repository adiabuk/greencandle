#!/usr/bin/env python
#pylint: disable=no-member, bare-except,too-many-locals, too-many-branches
"""
get data for all timeframes and pairs
output data to csv files
"""

import json
import sys
import csv
from collections import defaultdict
from greencandle.lib import config
from greencandle.lib.common import perc_diff, arg_decorator
from greencandle.lib.redis_conn import Redis

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
            except:
                continue

    if key == 'distance':
        data.append(['pair', 'direction', 'interval', 'distance'])
        for pair in pairs:
            for interval in intervals:
                try:
                    if float(res[interval][pair]['ohlc']['close']) > \
                            float(res[interval][pair]['upper_12']):

                        print(pair, "upper:{}".format(interval),
                              perc_diff(res[interval][pair]['ohlc']['close'],
                                        res[interval][pair]['upper_12']))
                        data.append([pair, "upper", interval,
                                     perc_diff(res[interval][pair]['ohlc']['close'],
                                               res[interval][pair]['upper_12'])])

                    elif float(res[interval][pair]['ohlc']['close']) < \
                            float(res[interval][pair]['lower_12']):

                        print(pair, "lower:{}".format(interval),
                              perc_diff(res[interval][pair]['ohlc']['close'],
                                        res[interval][pair]['lower_12']))
                        data.append([pair, "lower", interval,
                                     perc_diff(res[interval][pair]['ohlc']['close'],
                                               res[interval][pair]['lower_12'])])

                except:
                    pass
        with open('/data/aggregate/{}.csv'.format(key), 'w', encoding='UTF8', newline='') as handle:
            writer = csv.writer(handle)
            writer.writerows(data)

    else:
        data.append(['pair', '1m', '5m', '1h', '4h'])
        for pair in pairs:
            try:
                print(pair,
                      "1m:", res['1m'][pair][indicator],
                      "5m:", res['5m'][pair][indicator],
                      "1h:", res['1h'][pair][indicator],
                      "4h:", res['4h'][pair][indicator])
                data.append([pair,
                             res['1m'][pair][indicator],
                             res['5m'][pair][indicator],
                             res['1h'][pair][indicator],
                             res['4h'][pair][indicator]])

            except:
                continue
        with open('/data/aggregate/{}.csv'.format(key), 'w', encoding='UTF8', newline='') as handle:
            writer = csv.writer(handle)
            writer.writerows(data)
    print('DONE')

if __name__ == '__main__':
    main()