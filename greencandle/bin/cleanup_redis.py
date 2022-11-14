#!/usr/bin/env python
#pylint: disable=no-member

"""
Redis cleanup-script
"""

from greencandle.lib.redis_conn import Redis
from greencandle.lib.common import arg_decorator
from greencandle.lib import config

@arg_decorator
def main():
    """
    Cleanup old data from redis by all but the last 250 timeframes
    for all intervals
    Run through cron, using pairs in config
    """

    pairs = config.main.pairs.split()

    redis = Redis()
    config.create_config()
    count = 0
    for interval in ['1m', '3m', '5m', '15m', '30m', '1h', '4h', '1d']:
        for pair in pairs:
            pair = pair.strip()
            print("Analysing pair {}:{}".format(pair, interval))
            items = redis.get_items(pair, interval)
            for item in items[:-250]:
                redis.conn.hdel('{}:{}'.format(pair, interval), item)
                count += 1
    print("Deleted {} keys".format(count))


if __name__ == '__main__':
    main()
