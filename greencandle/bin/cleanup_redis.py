#!/usr/bin/env python
#pylint: disable=no-member

"""
Redis cleanup-script
"""
import sys
from greencandle.lib.redis_conn import Redis
from greencandle.lib.logger import get_logger
from greencandle.lib.common import arg_decorator
from greencandle.lib import config

@arg_decorator
def main():
    """
    Cleanup old data from redis by all but the last x timeframes
    for all intervals
    Run through cron, using pairs available in redis
    """
    logger = get_logger("cleanup_redis")
    redis = Redis()
    pairs = config.main.pairs.split()
    config.create_config()
    count = 0
    num = int(sys.argv[1]) if len(sys.argv) > 1 else 500
    for interval in ['1m', '3m', '5m', '15m', '30m', '1h', '4h', '12h', '1d']:
        for pair in pairs:
            pair = pair.strip()
            logger.debug("Analysing pair %s:%s", pair, interval)
            items = redis.get_intervals(pair, interval)
            for item in items[:-num]:
                redis.conn.hdel(f'{pair}:{interval}', item)
                count += 1
    logger.info("Deleted %s keys", count)
    del redis


if __name__ == '__main__':
    main()
