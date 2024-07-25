#pylint: disable=no-member
"""
Cleanup removed pairs from redis
"""
from greencandle.lib.common import arg_decorator
from greencandle.lib.redis_conn import Redis
from greencandle.lib import config

@arg_decorator
def main():
    """
    cycle through redis dbs and remove pairs not in config from all sets
    Run periodically using cron
    """
    config.create_config()
    pairs = config.main.pairs.split()

    redis_dbs = [5, 8, 9, 10]

    for rdb in redis_dbs:
        redis=Redis(db=rdb)
        keys = redis.conn.keys()

        for key in keys:
            for item in redis.conn.smembers(key):
                if item.decode().split(':')[0] not in pairs:
                    print(f"need to remove {item.decode()} {key} from db {rdb}")
                    redis.conn.srem(key, item)

if __name__ == '__main__':
    main()
