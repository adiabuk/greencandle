#!/usr/bin/env python
#pylint: disable=no-member,broad-exception-caught,import-error
"""
check freshness of redis data
"""
import sys
import datetime
import json
from send_nsca3 import send_nsca
from greencandle.lib import config
from greencandle.lib.redis_conn import Redis
from greencandle.lib.common import AttributeDict, arg_decorator
from greencandle.lib.logger import get_logger

@arg_decorator
def main():
    """
    check db0 of data env redis to ensure that all 1h entries for each trading pair
    has received an update for the current timeframe
    Run using cron a few mins past each hour
    """
    logger = get_logger(__name__)
    config.create_config()
    redis = Redis()
    interval = '1h'
    pairs = [x for x in config.main.pairs.split() if 'USDT' in x]
    all_times = set()
    actual_hour = datetime.datetime.now().hour
    for pair in pairs:
        try:
            item = redis.get_intervals(pair, interval)[-1]

            current = AttributeDict(json.loads(redis.get_item(f'{pair}:{interval}', item).decode()))
            hour = int(datetime.datetime.fromtimestamp(
                    int(current.ohlc['openTime'])/1000).strftime('%H'))
            all_times.add(hour)

        except Exception:
            pass

    if len(all_times) == 1 and actual_hour in all_times:
        msg = "OK: data is in sync"
        status= 0
    elif len(all_times) > 1 and actual_hour in all_times:
        # WARN
        msg = f"WARNING: some data not in sync.  Actual hour: {actual_hour}, found: {all_times}"
        status = 1
    elif actual_hour not in all_times and len(all_times) != 0:
        msg = f"CRITICAL: data is stale: Actual hour:{actual_hour}, found: {all_times}"
        status = 2
    else:
        #UNKOWN
        msg = "UNKNOWN: issue fetching data freshness: check redis and app"
        status = 3

    send_nsca(status=status, host_name='data', service_name='data_1h_freshness',
              text_output=msg, remote_host='nagios.amrox.loc')
    logger.info(msg)
    sys.exit(status)

if __name__ == '__main__':
    main()
