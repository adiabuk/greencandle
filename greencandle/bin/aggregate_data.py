#!/usr/bin/env python
#pylint: disable=no-member,bare-except,too-many-locals,too-many-branches,too-many-statements,no-else-return,unused-variable
"""
get data for all timeframes and pairs
output data to csv files
"""
import json
import sys
import os
import errno
from collections import defaultdict
import setproctitle
from greencandle.lib import config
from greencandle.lib.common import perc_diff, arg_decorator
from greencandle.lib.redis_conn import Redis

def get_bb_size(pair, interval, res, timeframe='200'):
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
        stx_from = last_res[interval][pair]['STX_22'][0]
        stx_to = res[interval][pair]['STX_22'][0]
        if stx_from == 1 and stx_to == -1:
            result = '-1'
        elif stx_from == -1 and stx_to == 1:
            result = '1'
        else:
            result = '0'
        return pair, interval, result
    except (TypeError, KeyError) as err:
        return None, None, 0

def get_volume(pair, interval, res):
    """
    get volume indicator
    """
    try:
        return res[interval][pair]['ohlc']['volume']
    except KeyError:
        return None

def get_num(pair, interval, res):
    """
    get volume indicator
    """
    try:
        return res[interval][pair]['ohlc']['numTrades']
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

def get_middle_distance(pair, interval, res, timeframe='200'):
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

def get_distance(pair, interval, res, timeframe='200'):
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
            return None, 0
        return direction, f'{distance_diff:.2f}'
    except KeyError:
        return None, 0

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

def aggregate_data(key, pairs, intervals, res, last_res, third_res):
    """
    create aggregate spreadsheets for given key using collected data
    """

    data = []
    if 'distance' in key:
        indicator = 'bb_200'
    else:
        indicator = key

    # all data in a single spreadsheet
    if key in ('all', 'redis'):
        redis_data = defaultdict()

        aggregates = ["distance_200", "stoch_flat", "bbperc_diff", "stx_diff",
                      "bb_size", "middle_200"]
        data.append(aggregates)
        for pair in pairs:
            for interval in intervals:
                distance_200 = get_distance(pair, interval, res, '200')[-1]
                middle_200 = get_middle_distance(pair, interval, res, '200')[-1]
                candle_size = get_candle_size(pair, interval, res, last_res)
                stoch_flat = get_stoch_flat(pair, interval, res, last_res)
                bb_size = get_bb_size(pair, interval, res)
                bbperc_diff = get_bbperc_diff(pair, interval, res, last_res)[-1]
                stx_diff = get_stx_diff(pair, interval, last_res, third_res)[-1]
                num = get_num(pair, interval, res)

                redis_data[f'{pair}:{interval}'] = \
                {
                 'distance_200': distance_200,
                 'candle_size': candle_size,
                 'middle_200': middle_200,
                 'stoch_flat': stoch_flat,
                 'bb_size': bb_size,
                 'stx_diff': stx_diff,
                 'num': num}

                data.append([pair, interval, distance_200, candle_size,
                             middle_200, stoch_flat, bb_size, bbperc_diff])

        # save to redis, overwriting previous value
        redis3 = Redis(db=3)
        for item, value in redis_data.items():
            value = {k:str(v) for k, v in value.items()}
            redis3.conn.hmset(item, value)

def collect_data():
    """
    get data for all timeframes and pairs
    output data to csv files
    """

    redis = Redis()
    key = sys.argv[1] if len(sys.argv) > 1 else None
    config.create_config()
    pairs = config.main.pairs.split()
    items = defaultdict(dict)
    res = defaultdict(dict)
    last_res = defaultdict(dict)
    third_res = defaultdict(dict)
    intervals = ['1m', '5m', '1h', '4h', '12h']

    aggregates = ["distance_200", "stoch_flat", "bbperc_diff", "stx_diff", "bb_size",
                  "all", "middle_200"]

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
                third_res[interval][pair] = json.loads(redis.get_item(f'{pair}:{interval}',
                                                                      items[interval][pair][-3])
                                                       .decode())

            except:
                continue

    aggregate_data('redis', pairs, intervals, res, last_res, third_res)

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
