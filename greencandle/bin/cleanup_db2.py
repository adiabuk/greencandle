#pylint: disable=no-member,too-few-public-methods
"""
Cleanup redis db2 from unused keys
"""

import re
from greencandle.lib.redis_conn import Redis
from greencandle.lib.mysql import Mysql
from greencandle.lib.common import get_be_services, list_to_dict, Bcolours, arg_decorator
from greencandle.lib import config

@arg_decorator
def main():
    """
    Cleanup redis db2 from unused keys
    Check open trades for matches and delete key if not found
    """
    config.create_config()

    dbase = Mysql()
    redis=Redis(db=2)
    open_trades = dbase.get_open_trades(name_filter='')
    keys = [x.decode() for x in redis.conn.keys()]

    short_dict = list_to_dict(get_be_services(config.main.base_env), reverse=True)
    print(config.main.base_env)
    for key in keys:
        orig_key = key
        try:
            pair, _, short = key.split(':')
            direction=short.split('-')[-1]
            #long_name = short_dict[short].rstrip(f'-{direction}')
            long_name = re.sub(rf'-{direction}', '', short_dict[short])

            res = [i for i in open_trades if i[2]== pair and i[3]==long_name and i[5]==direction]
            print(res)
            if not res:
                print(f"{Bcolours.FAIL}{orig_key} not used...deleting{Bcolours.ENDC}")
                redis.conn.delete(orig_key)   #delete here
            else:
                print(f"{Bcolours.OKGREEN}OK {orig_key} in use, ingoring...{Bcolours.ENDC}")
        except KeyError:
            print(f"{Bcolours.FAIL}{orig_key} not found in config...deleting{Bcolours.ENDC}")
            redis.conn.delete(orig_key)   #delete here
            continue

if __name__ == '__main__':
    main()
