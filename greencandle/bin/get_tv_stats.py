#!/usr/bin/env python
#pylint: disable=no-member,global-statement
"""
check tv sentiment
"""
import sys
from datetime import datetime
from tradingview_ta import get_multiple_analysis
from greencandle.lib.redis_conn import Redis
from greencandle.lib.common import arg_decorator
from greencandle.lib.objects import AttributeDict
from greencandle.lib import config
from greencandle.lib.logger import get_logger
from greencandle.lib.web import push_prom_data

@arg_decorator
def main():
    """
    Fetch sentiment from TV
    using available pairs and given interval
    interval is taken from argument, otherwise 1h is used
    """

    logger = get_logger(__name__)
    redis = Redis(db=15)
    assocs = {'STRONG_BUY': 2, 'BUY': 1, 'NEUTRAL':0, 'SELL': -1, 'STRONG_SELL': -2}
    stats = AttributeDict({x: 0 for x in assocs})  # set counter to 0
    config.create_config()
    interval = sys.argv[1] if len(sys.argv) > 1 else '1h'
    pairs = ['binance:' + s for s in config.main.pairs.split()]
    analysis = get_multiple_analysis(screener="crypto", interval=interval, symbols=pairs)
    for value in analysis.values():
        if value is None:
            continue
        stats[value.summary['RECOMMENDATION']] +=1

        redis.conn.rpush(f"{value.symbol}:{interval}", value.summary['RECOMMENDATION'])

    most = max(stats, key=stats.get)
    most_value = assocs[most]

    redis.conn.rpush(f"all:{interval}", most)

    logger.info("current sentiment for %s is %s, stats:%s", interval, most, stats)

    prom_data = {f'tv_strong_buy_{interval}': stats.STRONG_BUY,
                 f'tv_strong_sell_{interval}':  stats.STRONG_SELL,
                 f'tv_buy_{interval}': stats.BUY,
                 f'tv_sell_{interval}': stats.SELL,
                 f'tv_neutral_{interval}': stats.NEUTRAL}
    for promkey, promval in prom_data.items():
        push_prom_data(promkey, promval)
    push_prom_data(f'tv_all_value_{interval}', most_value)

if __name__ == '__main__':
    main()
