#!/usr/bin/env python
#pylint: disable=no-member,global-statement
"""
check tv sentiment
"""
import sys
import json
from datetime import datetime
from send_nsca3 import send_nsca
from tradingview_ta import get_multiple_analysis
from prometheus_client import CollectorRegistry, Gauge, push_to_gateway
from greencandle.lib.redis_conn import Redis
from greencandle.lib.common import arg_decorator, AttributeDict
from greencandle.lib import config


@arg_decorator
def main():
    """
    Fetch sentiment from TV
    using available pairs and given interval
    interval is taken from argument, otherwise 1h is used
    """
    redis = Redis(db=15)
    dt_stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    stats = AttributeDict({'STRONG_BUY':0, 'BUY':0, 'STRONG_SELL':0, 'SELL':0, 'NEUTRAL':0})
    config.create_config()
    env = config.main.base_env
    interval = sys.argv[1] if len(sys.argv) > 1 else '1h'
    pairs = ['binance:' + s for s in config.main.pairs.split()]
    analysis = get_multiple_analysis(screener="crypto", interval=interval, symbols=pairs)
    for v in analysis.values():
        if v is None:
            continue
        stats[v.summary['RECOMMENDATION']] +=1

        redis.conn.rpush(f"{v.symbol}:{interval}", v.summary['RECOMMENDATION'])
        filename = f'/data/tv_sentiment/{v.symbol}_{interval}_summary_{dt_stamp}.json'
        with open(filename, 'w', encoding="utf-8") as f:
            json.dump(v.summary, f)

    most = max(stats, key=stats.get)

    if 'STRONG' in most:
        status = 2
        msg = "CRITICAL"
    elif most in ['BUY', 'SELL']:
        status = 1
        msg = "WARNING"
    elif 'NEUTRAL' in most:
        status = 0
        msg = "OK"
    else:
        status = 3
        msg = "UNKNOWN"
    text = f"{msg}: current sentiment is {most}: {stats}"
    host = "data" if env == "data" else "jenkins"
    redis.conn.rpush(f"all:{interval}", most)
    send_nsca(status=status, host_name=host, service_name=f"{env}_tv_stats_{interval}",
              text_output=text, remote_host="nagios.amrox.loc")
    print(text)
    registry = CollectorRegistry()
    #stats = AttributeDict({'STRONG_BUY':0, 'BUY':0, 'STRONG_SELL':0, 'SELL':0, 'NEUTRAL':0})
    g1 = Gauge(f'tv_strong_buy_{interval}', 'TV strong-buy sentiment {interval}',
               registry=registry)
    g2 = Gauge(f'tv_strong_sell_{interval}', 'TV strong-sell sentiment {interval}',
               registry=registry)
    g3 = Gauge(f'tv_buy_{interval}', 'TV buy sentiment {interval}', registry=registry)
    g4 = Gauge(f'tv_sell_{interval}', 'TV buy sentiment {interval}', registry=registry)
    g5 = Gauge(f'tv_neutral_{interval}', 'TV neutral sentiment {interval}', registry=registry)

    g1.set(stats.STRONG_BUY)
    g2.set(stats.STRONG_SELL)
    g3.set(stats.BUY)
    g4.set(stats.SELL)
    g5.set(stats.NEUTRAL)
    push_to_gateway('jenkins:9091', job='data_metrics', registry=registry)

    sys.exit(status)

if __name__ == '__main__':
    main()
