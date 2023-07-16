#!/usr/bin/env python
#pylint: disable=no-member,bare-except,too-many-locals,too-many-branches,too-many-statements,no-else-return,unused-variable
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
import setproctitle
from greencandle.lib import config
from greencandle.lib.common import perc_diff, arg_decorator
from greencandle.lib.redis_conn import Redis

def get_bb_size(pair, interval, res, timeframe='12'):
    """
    percent between upper and lower bb
    """
    try:
        bb_diff = abs(perc_diff(res[interval][pair][f'bb_{timeframe}'][0],
                                res[interval][pair][f'bb_{timeframe}'][2]))
        bb_diff = f'{bb_diff:.2f}'
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
            return f"{value:.2f}" if value is not None else None
        elif "STOCH" in indicator:
            return f"{value[0]:.2f}", f"{value[1]:.2f}"
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
            value = f"{sum(res[interval][pair]['STOCHRSI_8'])/2:.2f}"

        elif round(sum(res[interval][pair]['STOCHRSI_8'])/2) <= 0 and \
                round(sum(last_res[interval][pair]['STOCHRSI_8'])/2) <= 0:
            value = f"{sum(res[interval][pair]['STOCHRSI_8'])/2:.2f}"
        else:
            value = None
        return value
    except (ValueError, KeyError):
        return None

def get_bbperc_diff(pair, interval, res, last_res):
    """
    get diff between current and previous bbperc value
    """
    try:
        bb_from = last_res[interval][pair]['bbperc_200']
        bb_to = res[interval][pair]['bbperc_200']
        diff = abs(bb_from - bb_to)
        return f'{bb_from:.2f}', f'{bb_to:.2f}', f'{diff:.2f}'
    except (TypeError, KeyError):
        return None, None, None

def get_stx_diff(pair, interval, res, last_res):
    """
    Get change in supertrend direction
    """
    try:
        stx_from = last_res[interval][pair]['STX_200']
        stx_to = res[interval][pair]['STX_200']
        if stx_from == 1 and stx_to == -1:
            result = 'down'
        elif stx_from == -1 and stx_to == 1:
            result = 'up'
        else:
            result = 'hodl'
        return pair, interval, result
    except (TypeError, KeyError) as err:
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

        return f'{max_diff:.2f}'
    except:
        return None

def get_middle_distance(pair, interval, res, timeframe='12'):
    """
    get distance between to middle bollinger band as a percentage
    """

    try:

        distance = perc_diff(res[interval][pair]['ohlc']['close'],
                             res[interval][pair]['bb_'+timeframe][1])
        if distance > 0:
            direction = 'below'
        else:
            direction = 'above'
        return direction, f'{abs(distance):.2f}'
    except KeyError:
        return None, None

def get_distance(pair, interval, res, timeframe='12'):
    """
    get distance between upper/lower bollinger bands
    and current price as a percentage if above/below
    """

    try:
        # upper
        if float(res[interval][pair]['ohlc']['close']) > \
                 float(res[interval][pair]['bb_'+timeframe][0]):

            distance_diff = abs(perc_diff(res[interval][pair]['ohlc']['close'],
                                          res[interval][pair]['bb_'+timeframe][0]))
            direction = 'upper'
        # lower
        elif float(res[interval][pair]['ohlc']['close']) < \
                 float(res[interval][pair]['bb_'+timeframe][2]):
            distance_diff = abs(perc_diff(res[interval][pair]['ohlc']['close'],
                                          res[interval][pair]['bb_'+timeframe][2]))
            direction = 'lower'
        else:
            return None, None
        return direction, f'{distance_diff:.2f}'
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

def aggregate_data(key, pairs, intervals, res, last_res):
    """
    create aggregate spreadsheets for given key using collected data
    """

    data = []
    if 'distance' in key:
        indicator = 'bb_12'
    else:
        indicator = key

    # stochf k,d maxed out
    if key == 'stoch_flat':
        data.append(['pair', 'interval', 'avg'])
        for pair in pairs:
            for interval in intervals:
                stoch_flat = get_stoch_flat(pair, interval, res, last_res)
                data.append([pair, interval, stoch_flat])

    # change in supertrend direction
    elif key == 'stx_diff':
        data.append(['pair', 'interval', 'from', 'to', 'direction'])
        for pair in pairs:
            for interval in intervals:
                stx_from, stx_to, direction = get_stx_diff(pair, interval, res, last_res)
                if direction:
                    data.append([pair, interval, stx_from, stx_to, direction])
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
        data.append(['pair', 'interval', 'size'])
        for pair in pairs:
            for interval in intervals:
                max_diff = get_candle_size(pair, interval, res, last_res)
                if max_diff:
                    data.append([pair, interval, max_diff])

    # distance between current price and edge of upper/lower bollinger bands
    elif 'distance' in key:
        data.append(['pair', 'interval', 'direction', 'distance'])
        for pair in pairs:
            for interval in intervals:
                _, timeframe = key.split('_')
                direction, distance_diff = get_distance(pair, interval, res, timeframe)
                if direction:
                    data.append([pair, interval, direction, distance_diff])

    # distance to middle bb
    elif 'middle' in key:
        data.append(['pair', 'interval', 'direction', 'distance'])
        for pair in pairs:
            for interval in intervals:
                _, timeframe = key.split('_')
                direction, distance_diff = get_middle_distance(pair, interval, res, timeframe)
                if direction:
                    data.append([pair, interval, direction, distance_diff])

    # all data in a single spreadsheet
    elif key in ('all', 'redis'):
        redis_data = defaultdict()
        data.append(['pair', 'interval', 'distance_12', 'distance_200', 'candle_size',
                     'middle_12', 'middle_200', 'stoch_flat', 'bb_size',
                     'bbperc_diff', 'bbperc_200', 'stoch', 'stx_200', 'stx_diff'])
        for pair in pairs:
            for interval in intervals:
                distance_12 = get_distance(pair, interval, res, '12')[-1]
                distance_200 = get_distance(pair, interval, res, '200')[-1]
                candle_size = get_candle_size(pair, interval, res, last_res)

                _, middle_12 = get_middle_distance(pair, interval, res, '12')
                _, middle_200 = get_middle_distance(pair, interval, res, '200')

                stoch_flat = get_stoch_flat(pair, interval, res, last_res)
                bb_size = get_bb_size(pair, interval, res)
                bbperc_diff = get_bbperc_diff(pair, interval, res, last_res)[-1]
                vol = get_volume(pair, interval, res)
                bbperc_200 = get_indicator_value(pair, interval, res, 'bbperc_200')
                stx_200 = get_indicator_value(pair, interval, res, 'STX_200')
                stx_diff = get_stx_diff(pair, interval, res, last_res)[-1]
                stoch = get_indicator_value(pair, interval, res, 'STOCHRSI_8')
                redis_data[f'{pair}:{interval}'] = \
                {'distance_12':distance_12, 'distance_200': distance_200,
                 'candle_size': candle_size, 'middle_12': middle_12, 'middle_200': middle_200,
                 'stoch_flat': stoch_flat, 'bb_size': bb_size, 'bbperc_200': bbperc_200,
                 'stx_diff': stx_diff}

                data.append([pair, interval, distance_12, distance_200, candle_size, middle_12,
                             middle_200, stoch_flat, bb_size, bbperc_diff, bbperc_200, stoch,
                             stx_200])

        # save to redis, overwriting previous value
        redis3 = Redis(db=3)
        for item, value in redis_data.items():
            value = {k:str(v) for k, v in value.items()}
            redis3.conn.hmset(item, value)
        if key == 'redis':
            return

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
    with open(f'/data/aggregate/{key}_{timestr}.csv',
              'w', encoding='UTF8', newline='') as handle:
        writer = csv.writer(handle)
        writer.writerows(data)

    # save as tsv
    with open(f'/data/aggregate/{key}_{timestr}.tsv',
              'w', encoding='UTF8', newline='') as handle:
        # remove spaces from lists for cmd line parsing
        new_list = [[str(x).replace(' ', '') for x in y] for y in data]
        writer = csv.writer(handle, delimiter='\t')
        writer.writerows(new_list)

    # create/overwrite symlink to most recent file
    os.chdir('/data/aggregate')
    symlink_force(f'../{key}_{timestr}.tsv', 'current/{key}.tsv')
    symlink_force(f'../{key}_{timestr}.csv', 'current/{key}.csv')

def collect_data():
    """
    get data for all timeframes and pairs
    output data to csv files
    """

    redis = Redis()
    key = sys.argv[1] if len(sys.argv) > 1 else None
    config.create_config()
    pair_set = set()
    for item in redis.conn.scan_iter("*:12h"):
        pair_set.add(item.decode().split(":")[0])
    pairs = list(pair_set)
    items = defaultdict(dict)
    res = defaultdict(dict)
    last_res = defaultdict(dict)
    intervals = ['1m', '5m', '1h', '4h', '12h']

    aggregates = ["distance_12", "distance_200", "bbperc_200", "STOCHRSI_8", "STX_200",
                  "stoch_flat", "bbperc_diff", "stx_diff", "volume", "bb_size", "all",
                  "middle_200", "middle_12"]

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
                res[interval][pair] = json.loads(redis.get_item(f'{pair}:{interval}',
                                                                items[interval][pair][-1]).decode())
                last_res[interval][pair] = json.loads(redis.get_item(f'{pair}:{interval}',
                                                                     items[interval][pair][-2])
                                                      .decode())

            except:
                continue
    if key == 'keys':
        items_1h = redis.get_items('BTCUSDT', '1h')
        keys = json.loads(redis.get_item('BTCUSDT:1h', items_1h[-1]).decode()).keys()
        sys.exit()
    aggregate_data('redis', pairs, intervals, res, last_res)

@arg_decorator
def main():
    """
    main function
    """
    setproctitle.setproctitle('aggregate_data')
    while True:
        collect_data()

if __name__ == '__main__':
    main()
