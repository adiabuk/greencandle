#pylint: disable=no-member
"""
Cleanup removed pairs from redis
"""
from greencandle.lib.common import arg_decorator
from greencandle.lib.redis_conn import Redis
from greencandle.lib import config
from greencandle.lib.logger import get_logger

@arg_decorator
def main():
    """
    cycle through redis dbs and remove pairs not in config from all sets
    Run periodically using cron
    """

    logger = get_logger(__name__)
    config.create_config()
    pairs = config.main.pairs.split()
    redis_dbs = [4, 5, 8, 9, 10, 13]

    for rdb in redis_dbs:
        redis=Redis(db=rdb)
        keys = redis.conn.keys()

        for key in keys:
            for item in redis.conn.smembers(key):
                if item.decode().split(':')[0] not in pairs:
                    logger.info("removing %s %s from db %s", item.decode(), key, rdb)
                    redis.conn.srem(key, item)

if __name__ == '__main__':
    main()
