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
from greencandle.lib.common import arg_decorator, AttributeDict
from greencandle.lib import config


@arg_decorator
def main():
    """
    Fetch sentiment from TV
    using available pairs and given interval
    interval is taken from argument, otherwise 1h is used
    """
    dt_stamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    stats = AttributeDict({'buy':0, 'sell':0, 'neutral':0})
    config.create_config()
    env = config.main.base_env
    interval = sys.argv[1] if len(sys.argv) > 1 else '1h'
    pairs = ['binance:' + s for s in config.main.pairs.split()]
    analysis = get_multiple_analysis(screener="crypto", interval=interval, symbols=pairs)
    for v in analysis.values():
        if 'BUY' in v.summary['RECOMMENDATION']:
            stats.buy += 1
        elif 'SELL' in v.summary['RECOMMENDATION']:
            stats.sell += 1
        if 'NEUTRAL' in v.summary['RECOMMENDATION']:
            stats.neutral += 1

        filename = f'/data/tv_sentiment/{v.symbol}_{interval}_summary_{dt_stamp}.json'
        with open(filename, 'w', encoding="utf-8") as f:
            json.dump(v.summary, f)

    print(stats)
    most = max(stats, key=stats.get)

    perf = ' '.join(f'{key}={value}' for key, value in stats.items())
    print(perf)
    warn = 100
    crit = 200
    if stats[most] > crit:
        status = 2
        msg = "CRITICAL"
    elif stats[most] > warn:
        status = 1
        msg = "WARNING"
    elif stats[most] < 100:
        status = 0
        msg = "OK"
    else:
        status = 3
        msg = "UNKNOWN"
    text = f"{msg}: current sentiment is {most}|{perf};{warn};{crit};;"

    host = "data" if env == "data" else "jenkins"
    send_nsca(status=status, host_name=host, service_name=f"{env}_tv_stats_{interval}",
              text_output=text, remote_host="nagios.amrox.loc")
    print(text)
    sys.exit(status)

if __name__ == '__main__':
    main()
