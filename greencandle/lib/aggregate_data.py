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
from greencandle.lib import config
from greencandle.lib.common import perc_diff, epoch2date
from greencandle.lib.redis_conn import Redis
from greencandle.lib.logger import get_logger

LOGGER = get_logger(__name__)

def get_empty_count(res):
    """
    Get number of empty (zero trade) enties in sample given
    """
    count = 0

    for _, item in res.items():
        try:
            if int(item['ohlc']['numTrades']) < 1:
                count +=1
        except:
            continue
    return count

def get_atrp_equal(res):
    """
    Number of candles where ATRp > 75
    Use last 10 items
    """
    count = 0
    for item in list(res.items())[-10:]:
        try:
            if float(item[-1]['ATRp_30']) > 75:
                count +=1

        except:
            continue
    return count

def get_macd_xover(res, last_res, timeframe=19):
    """ get MACD crossover long or short"""

    xover = 0
    try:
        if res[f'MACD_{timeframe}'][0] < res[f'MACD_{timeframe}'][1] and \
                last_res[f'MACD_{timeframe}'][0] > last_res[f'MACD_{timeframe}'][1]:
            xover = -1   # short
        elif res[f'MACD_{timeframe}'][0] > res[f'MACD_{timeframe}'][1] and \
                last_res[f'MACD_{timeframe}'][0] < last_res[f'MACD_{timeframe}'][1]:
            xover = 1  # long
        else:
            xover = 0  # no cross
    except:
        xover = 0
    return xover

def get_bb_size(res, timeframe='200'):
    """
    percent between upper and lower bb
    """
    try:
        bb_diff = abs(perc_diff(res[f'bb_{timeframe}'][0],
                                res[f'bb_{timeframe}'][2]))
        bb_diff = f'{bb_diff:.2f}'
    except KeyError:
        bb_diff = ''

    return bb_diff

def get_indicator_value(res, indicator):
    """
    get value of indicator
    """
    try:
        value = res[indicator]
        if "bbperc" in indicator:
            return f"{value:.2f}" if value is not None else None
        elif "STOCH" in indicator:
            return f"{value[0]:.2f}", f"{value[1]:.2f}"
        else:
            return value
    except KeyError:
        return None, None

def get_stoch_flat(res, last_res):
    """
    Get stoch value if k,d maxed out or bottomed out
    """
    try:
        if round(sum(res['STOCHRSI_8'])/2) >= 100 and \
                round(sum(last_res['STOCHRSI_8'])/2) >= 100:
            value = f"{sum(res['STOCHRSI_8'])/2:.2f}"

        elif round(sum(res['STOCHRSI_8'])/2) <= 0 and \
                round(sum(last_res['STOCHRSI_8'])/2) <= 0:
            value = f"{sum(res['STOCHRSI_8'])/2:.2f}"
        else:
            value = None
        return value
    except (ValueError, KeyError):
        return None

def get_bbperc_diff(res, last_res):
    """
    get diff between current and previous bbperc value
    """
    try:
        bb_from = last_res['bbperc_200']
        bb_to = res['bbperc_200']
        diff = abs(bb_from - bb_to)
        return round(bb_from, 4), round(bb_to, 4), round(diff, 4)
    except (TypeError, KeyError):
        return -1, -1, -1

def get_stx_diff(res, last_res):
    """
    Get change in supertrend direction
    """
    try:
        stx_from = last_res['STX_22'][0]
        stx_to = res['STX_22'][0]
        if stx_from == 1 and stx_to == -1:
            result = '-1'
        elif stx_from == -1 and stx_to == 1:
            result = '1'
        else:
            result = '0'
        return result
    except (TypeError, KeyError) as err:
        return None, None, 0

def get_volume(res):
    """
    get volume indicator
    """
    try:
        return res['ohlc']['volume']
    except KeyError:
        return None

def get_ohlc_attr(res, attr):
    """
    get ohlc attribute
    """
    try:
        return res['ohlc'][attr]
    except KeyError:
        return None

def get_candle_size(res):
    """
    get size of current candle compared to previous
    """
    try:
        max_diff = abs(perc_diff(res['ohlc']['high'],
                                 res['ohlc']['low']))

        return f'{max_diff:.6f}'
    except:
        return None

def get_macd_diff(res, timeframe=19):
    """
    get perc diff between macd and signal lines
    """

    try:
        diff = perc_diff(res[f'MACD_{timeframe}'][1], res[f'MACD_{timeframe}'][0])
    except:
        diff = 0
    return round(diff, 4)

def get_middle_distance(res, timeframe='200'):
    """
    get distance between to middle bollinger band as a percentage
    """

    try:

        distance = perc_diff(res['ohlc']['close'],
                             res['bb_'+timeframe][1])
        if distance > 0:
            direction = 'below'
        else:
            direction = 'above'
        return direction, f'{abs(distance):.2f}'
    except KeyError:
        return None, None

def get_distance(res, timeframe='200'):
    """
    get distance between upper/lower bollinger bands
    and current price as a percentage if above/below
    """

    try:
        # upper
        if float(res['ohlc']['close']) > \
                 float(res['bb_'+timeframe][0]):

            distance_diff = abs(perc_diff(res['ohlc']['close'],
                                          res['bb_'+timeframe][0]))
            direction = 'upper'
        # lower
        elif float(res['ohlc']['close']) < \
                 float(res['bb_'+timeframe][2]):
            distance_diff = abs(perc_diff(res['ohlc']['close'],
                                          res['bb_'+timeframe][2]))
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

def average(lst):
    """
    Get average from list of values
    """
    return sum(lst) / len(lst)

def get_avg_candles(data):
    """
    get average candle size across number of candles provided
    """
    diffs = []
    for item in list(data.keys())[-6:-1]:
        try:
            diffs.append(perc_diff(data[item]['ohlc']['low'],
                                   data[item]['ohlc']['high']))
        except:
            pass
    if diffs:
        return round(average(diffs), 6)
    return 0

def get_sum_candles(data):
    """
    get sum of candle size across number of candles provided
    """
    diffs = []
    for item in list(data.keys())[:-1]:
        try:
            diffs.append(perc_diff(data[item]['ohlc']['low'],
                                   data[item]['ohlc']['high']))
        except:
            pass
    if diffs:
        return round(sum(diffs), 6)
    return 0

def aggregate_data(key, pairs, interval, data, items):
    """
    create aggregate spreadsheets for given key using collected data
    """
    if 'distance' in key:
        indicator = 'bb_200'
    else:
        indicator = key

    # all data in a single spreadsheet
    if key in ('all', 'redis'):
        redis_data = defaultdict()
        for pair in pairs:
            current_item = items[interval][pair]
            res = data[interval][pair][current_item[-1]]
            last_res = data[interval][pair][current_item[-2]]
            third_res = data[interval][pair][current_item[-3]]

            distance_200 = get_distance(res, '200')[-1]
            middle_200 = get_middle_distance(res, '200')[-1]
            candle_size = get_candle_size(res)
            stoch_flat = get_stoch_flat(res, last_res)
            bb_size = get_bb_size(res)
            macd_xover = get_macd_xover(last_res, third_res,'19')
            macd_diff = get_macd_diff(res, '19')
            bbperc_diff = get_bbperc_diff(res, last_res)[-1]
            stx_diff = get_stx_diff(last_res, third_res)
            avg_candles = get_avg_candles(data[interval][pair])
            sum_candles = get_sum_candles(data[interval][pair])
            num = get_ohlc_attr(res, 'numTrades')
            date = get_ohlc_attr(res, 'openTime')
            humandate = epoch2date(int(int(date)/1000))
            bbperc = res['bbperc_200']
            rsi = f'{res["RSI_7"]:.2f}'
            cci = f'{res["CCI_100"]:.2f}'
            atrp = res['ATRp_30']
            empty_count = get_empty_count(data[interval][pair])
            atrp_equal = get_atrp_equal(data[interval][pair])
            redis_data[f'{pair}:{interval}'] = \
            {
             'distance_200': distance_200,
             'candle_size': candle_size,
             'avg_candles': avg_candles,
             'sum_candles': sum_candles,
             'middle_200': middle_200,
             'stoch_flat': stoch_flat,
             'bbperc': bbperc,
             'macd_xover': macd_xover,
             'macd_diff': macd_diff,
             'bb_size': bb_size,
             'stx_diff': stx_diff,
             'bbperc_diff': bbperc_diff,
             'empty_count': empty_count,
             'atrp': atrp,
             'rsi': rsi,
             'cci': cci,
             'num': num,
             'atrp_equal': atrp_equal,
             'date': humandate}

        # save to redis, overwriting previous value
        redis3 = Redis(db=3)
        for item, value in redis_data.items():
            value = {k:str(v) for k, v in value.items()}
            redis3.conn.hmset(item, value)

def collect_agg_data(interval):
    """
    get data for all timeframes and pairs
    output data to csv files
    """

    LOGGER.debug("starting aggregate run")
    redis = Redis()
    key = sys.argv[1] if len(sys.argv) > 1 else None
    config.create_config()
    pairs = config.main.pairs.split()
    items = defaultdict(dict)
    data = defaultdict(dict)

    ###
    # Collect timeframes (milliepochs) for each pair/interval
    samples = 20
    for pair in pairs:
        try:
            items[interval][pair] = redis.get_items(pair=pair,
                                                    interval=interval)[-int(samples):]
        except:
            continue

    # Collect data for each pair/interval
    for pair in pairs:
        data[interval][pair] = {}

        for item in items[interval][pair]:
            try:
                data[interval][pair][item] = json.loads(redis.get_item(f'{pair}:{interval}',
                                                                       item).decode())
            except:
                continue
    ###
    aggregate_data('redis', pairs, interval, data, items)
    LOGGER.debug("Finishing aggregate run")
