#pylint: disable=no-member,too-few-public-methods
"""
Cleanup redis db0 keys
Not to be run in data env
"""

from greencandle.lib.redis_conn import Redis
from greencandle.lib.mysql import Mysql
from greencandle.lib.common import arg_decorator
from greencandle.lib import config

@arg_decorator
def main():
    """
    Cleanup redis db0 from unused keys
    Check open trades for matches on pair and interval
    DO NOT RUN IN DATA ENV
    """
    config.create_config()

    dbase = Mysql()
    redis=Redis(db=0)
    open_trades = dbase.get_open_trades(name_filter='')
    keys = [x.decode() for x in redis.conn.keys()]

    print(config.main.base_env)
    for key in keys:
        pair, interval = key.split(':')

        res = [i for i in open_trades if i[2]== pair and i[1]==interval]
        if not res:
            print(f"We need to delete {key}")
            redis.conn.delete(key)   #delete here

if __name__ == '__main__':
    main()
