#pylint: disable=no-member
"""
Cleanup script for redis data env
"""
from greencandle.lib.redis_conn import Redis
from greencandle.lib.common import arg_decorator
from greencandle.lib import config
from greencandle.lib.logger import get_logger


@arg_decorator
def main():
    """
    Cleanup pairs that have been removed from data env
    redis - dbs 0 and 3 ohlc and agg data.
    Run periodically using cron in data env only
    """

    logger = get_logger(__name__)
    config.create_config()
    pairs = config.main.pairs.split()

    for redis_db in [0,3]:
        redis=Redis(db=redis_db)

        keys = redis.conn.keys()
        for key in keys:
            current_pair = key.decode().split(':')[0]
            if current_pair not in pairs:
                logger.info("deleting key %s", key)
                redis.conn.delete(key)

if __name__ == '__main__':
    main()
