#!/usr/bin/env python
#pylint: disable=no-member, logging-not-lazy

"""
Redis cleanup-script
"""

import re
from greencandle.lib.redis_conn import Redis
from greencandle.lib.logger import get_logger
from greencandle.lib.common import arg_decorator
from greencandle.lib import config

@arg_decorator
def main():
    """
    Cleanup old data from redis by all but the last 250 timeframes
    for all intervals
    Run through cron, using pairs available in redis
    """
    logger = get_logger("cleanup_redis")
    redis = Redis()
    pairs = set()
    # Get unique set of uppercase pairs from redis keys
    for key in redis.conn.keys():
        if re.match('([A-Z]+):.*h', key.decode()):
            pairs.add(re.findall('([A-Z]+):.*[hm]', key.decode())[0])
    # convert set to list
    pairs = list(pairs)

    config.create_config()
    count = 0
    for interval in ['1m', '3m', '5m', '15m', '30m', '1h', '4h', '1d']:
        for pair in pairs:
            pair = pair.strip()
            logger.info("Analysing pair %s:%s" %(pair, interval))
            items = redis.get_items(pair, interval)
            for item in items[:-500]:
                redis.conn.hdel('{}:{}'.format(pair, interval), item)
                count += 1
    logger.info("Deleted %s keys" % count)


if __name__ == '__main__':
    main()
