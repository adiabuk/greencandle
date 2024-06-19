#pylint: disable=no-member
"""
Cleanup script for redis data env
"""
from greencandle.lib.redis_conn import Redis
from greencandle.lib.common import arg_decorator
from greencandle.lib import config


@arg_decorator
def main():
    """
    Cleanup pairs that have been removed from data env
    redis - dbs 0 and 3 ohlc and agg data.
    Run periodically using cron in data env only
    """

    config.create_config()

    pairs = config.main.pairs.split()

    for redis_db in [0,3]:
        redis=Redis(db=redis_db)

        keys = redis.conn.keys()
        for key in keys:
            current_pair = key.decode().split(':')[0]
            if current_pair not in pairs:
                print(f"deleting {key}")
                redis.conn.delete(key)

if __name__ == '__main__':
    main()
