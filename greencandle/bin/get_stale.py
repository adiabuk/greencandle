#pylint: disable=no-member
"""
Find redis keys that don't correspond to open trades
"""
from greencandle.lib.common import arg_decorator
from greencandle.lib.redis_conn import Redis
from greencandle.lib import config
from greencandle.lib.mysql import Mysql
from greencandle.lib.common import get_be_services, list_to_dict

@arg_decorator
def main():
    """
    Find redis keys that don't correspond to open trades
    Usage: get_stale
    """

    config.create_config()
    dbase = Mysql()
    redis = Redis(db=2)
    keys = redis.conn.keys()
    for key in keys:
        pair, short, _ = key.decode().split(':')
        name = list_to_dict(get_be_services(config.main.base_env), reverse=True)[short]
        direction = name.split('-')[-1]
        if not dbase.trade_in_context(pair, name.strip('-{}'.format(direction)), direction):
            print("{} not available in context".format(key.decode()))
    print("DONE")
if __name__ == '__main__':
    main()
