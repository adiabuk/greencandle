#!/usr/bin/env python
#pylint: disable=no-member,bare-except,too-many-locals,too-many-branches,too-many-statements
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

def get_indicator_value(pair, interval, res, indicator):
    """
    get value of indicator
    """
    try:
        value = res[interval][pair][indicator]
        if "bbperc" in indicator:
            return "{:.2f}".format(value) if value is not None else None
        elif "STOCH" in indicator:
            return "{:.2f}".format(value[0]), "{:.2f}".format(value[1])
        else:
            return value
    except KeyError:
        return None, None

def get_stoch_flat(pair, interval, res, last_res):
    """
    Get stoch value if k,d maxed out or bottomed out
    """
    try:
        if round(sum(res[interval][pair]['STOCHRSI_8'])/2) >= 100 and \
                round(sum(last_res[interval][pair]['STOCHRSI_8'])/2) >= 100:
            value = '{:.2f}'.format(sum(res[interval][pair]['STOCHRSI_8'])/2)

        elif round(sum(res[interval][pair]['STOCHRSI_8'])/2) <= 0 and \
                round(sum(last_res[interval][pair]['STOCHRSI_8'])/2) <= 0:
            value = '{:.2f}'.format(sum(res[interval][pair]['STOCHRSI_8'])/2)
        else:
            value = None
        return value
    except KeyError:
        return None

def get_bbperc_diff(pair, interval, res, last_res):
    """
    get diff between current and previous bbperc value
    """
    try:
        bb_from = last_res[interval][pair]['bbperc_200']
        bb_to = res[interval][pair]['bbperc_200']
        diff = abs(bb_from - bb_to)
        return '{:.2f}'.format(bb_from), '{:.2f}'.format(bb_to), '{:.2f}'.format(diff)
    except (TypeError, KeyError):
        return None, None, None

def get_volume(pair, interval, res):
    """
    get volume indicator
    """
    try:
        return res[interval][pair]['ohlc']['volume']
    except KeyError:
        return None

def get_candle_size(pair, interval, res, last_res):
    """
    get size of current candle compared to previous
    """
    try:
        max_diff = max(abs(perc_diff(res[interval][pair]['ohlc']['high'],
                                     last_res[interval][pair]['ohlc']['low'])),
                       abs(perc_diff(res[interval][pair]['ohlc']['low'],
                                     last_res[interval][pair]['ohlc']['high'])))

        return '{:.2f}'.format(max_diff)
    except:
        return None

def get_distance(pair, interval, res):
    """
    get distance between upper and lower bollinger bands as a percentage
    """

    try:
        if float(res[interval][pair]['ohlc']['close']) > \
                 float(res[interval][pair]['upper_12']):

            distance_diff = abs(perc_diff(res[interval][pair]['ohlc']['close'],
                                          res[interval][pair]['upper_12']))
            direction = 'upper'

        elif float(res[interval][pair]['ohlc']['close']) < \
                 float(res[interval][pair]['lower_12']):
            distance_diff = abs(perc_diff(res[interval][pair]['ohlc']['close'],
                                          res[interval][pair]['lower_12']))
            direction = 'lower'
        else:
            return None, None
        return direction, '{:.2f}'.format(distance_diff)
    except KeyError:
        return None, None

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
                stoch_flat = get_stoch_flat(pair, interval, res, last_res)
                data.append([pair, interval, stoch_flat])

    # volume
    elif key == 'volume':
        data.append(['pair', 'interval', 'volume'])
        for pair in pairs:
            for interval in intervals:
                vol = get_volume(pair, interval, res)
                if vol:
                    data.append([pair, interval, vol])

    # percent between upper and lower bb
    elif key == 'bb_size':
        data.append(['pair', 'interval', 'bb_size'])
        for pair in pairs:
            for interval in intervals:
                bb_diff = get_bb_size(pair, interval, res)
                data.append([pair, interval, bb_diff])

    # rapid change in bbperc value
    elif key == 'bbperc_diff':
        data.append(['pair', 'interval', 'from', 'to', 'diff'])
        for pair in pairs:
            for interval in intervals:
                bb_from, bb_to, bb_diff = get_bbperc_diff(pair, interval, res, last_res)
                if bb_diff:
                    data.append([pair, interval, bb_from, bb_to, bb_diff])

    # change in candle size
    elif key == 'candle_size':
        data.append(['pair', 'interval', 'key'])
        for pair in pairs:
            for interval in intervals:
                max_diff = get_candle_size(pair, interval, res, last_res)
                if max_diff:
                    data.append([pair, interval, max_diff])

    # distance between current price and edge of upper/lower bollinger bands
    elif key == 'distance':
        data.append(['pair', 'interval', 'direction', 'distance'])
        for pair in pairs:
            for interval in intervals:
                direction, distance_diff = get_distance(pair, interval, res)
                if direction:
                    data.append([pair, interval, direction, distance_diff])

    # all data in a single spreadsheet
    elif key == 'all':
        data.append(['pair', 'interval', 'distance', 'candle_size', 'stoch_flat', 'bb_size',
                     'bbperc_diff', 'volume', 'upper', 'middle', 'lower', 'bbperc_200', 'stoch'])
        for pair in pairs:
            for interval in intervals:
                distance = get_distance(pair, interval, res)[-1]
                candle_size = get_candle_size(pair, interval, res, last_res)
                stoch_flat = get_stoch_flat(pair, interval, res, last_res)
                bb_size = get_bb_size(pair, interval, res)
                bbperc_diff = get_bbperc_diff(pair, interval, res, last_res)[-1]
                vol = get_volume(pair, interval, res)
                upper = get_indicator_value(pair, interval, res, 'upper_12')
                middle = get_indicator_value(pair, interval, res, 'middle_12')
                lower = get_indicator_value(pair, interval, res, 'lower_12')
                bbperc_200 = get_indicator_value(pair, interval, res, 'bbperc_200')
                stoch = get_indicator_value(pair, interval, res, 'STOCHRSI_8')
                data.append([pair, interval, distance, candle_size, stoch_flat, bb_size,
                             bbperc_diff, vol, upper, middle, lower, bbperc_200, stoch])

    # indicator data
    else:
        data.append(['pair', 'interval', indicator])
        for pair in pairs:
            for interval in intervals:
                value = get_indicator_value(pair, interval, res, indicator)
                if value:
                    data.append([pair, interval, value])

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
