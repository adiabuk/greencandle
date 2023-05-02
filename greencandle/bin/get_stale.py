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
    bad_keys = []
    for key in keys:
        try:
            pair, _, short = key.decode().split(':')
            name = list_to_dict(get_be_services(config.main.base_env), reverse=True)[short]
        except (KeyError, ValueError):
            bad_keys.append(key.decode())
            continue
        direction = name.split('-')[-1]
        if not dbase.trade_in_context(pair, name.rsplit('-', 1)[0], direction):
            bad_keys.append(key.decode())

    if bad_keys:
        print("Bad Keys.....")
        for key in bad_keys:
            print(key)
        user_input = input('delete? (y/n): ')
        if user_input.lower() == 'y':
            for key in bad_keys:
                redis.conn.delete(key)
        else:
            print('exiting')
    else:
        print('no bad keys found')

    print("DONE")
if __name__ == '__main__':
    main()
