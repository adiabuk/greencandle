#!/usr/bin/env python
"""
Set/unset drain status for a given direction depending on trend
"""
import sys
from greencandle.lib.redis_conn import Redis
from greencandle.lib.web import set_drain, get_drain_env
from greencandle.lib.logger import get_logger
from greencandle.lib.common import arg_decorator


@arg_decorator
def main():
    """
    Check for trend using TV data in redis
    Check that trading in opposite direction is blocked in drain api
    If not, set drain.
    Also set drain for both directions if result is neutral, or not available
    Usage: tv_drain [env] [interval] [check_intervals]
    """

    def get_and_set(direction, status):
        """
        Check if drain status matches what we need it to be
        If not, set and log
        """
        if current_drain[f'tf_{interval}'][direction] != status:
            logger.info("Setting %s %s %s to %s", env, interval, direction, status)
            set_drain(env=env, interval=interval, direction=direction, value=status)


    env = sys.argv[1]
    current_drain = get_drain_env(env)
    logger = get_logger(__name__)
    redis = Redis(db=15)
    interval = sys.argv[2]
    check_intervals = sys.argv[3].split(',')
    results = []
    for check_interval in check_intervals:
        current = redis.conn.lrange(f'all:{check_interval}', -20,-1)[-1].decode()
        results.append(current)

    if all("SELL" in item for item in results):
        get_and_set('long', True)
        get_and_set('short', False)
    elif all("BUY" in item for item in results):
        get_and_set('long', False)
        get_and_set('short', True)
    else:
        get_and_set('long', True)
        get_and_set('short', True)

if __name__ == '__main__':
    main()
