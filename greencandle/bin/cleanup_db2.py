#pylint: disable=no-member,too-few-public-methods
"""
Cleanup redis db2 from unused keys
"""

from greencandle.lib.redis_conn import Redis
from greencandle.lib.mysql import Mysql
from greencandle.lib.common import arg_decorator
from greencandle.lib.common import get_be_services, list_to_dict
from greencandle.lib import config

class Bcolors:
    """
    Unicode colors for text hilighting
    """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

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
            long_name = short_dict[short].rstrip(f'-{direction}')
            res = [i for i in open_trades if i[2]== pair and i[3]==long_name and i[5]==direction]
            if not res:
                print(f"{Bcolors.FAIL}{orig_key} not used...deleting{Bcolors.ENDC}")
                redis.conn.delete(orig_key)   #delete here
            else:
                print(f"{Bcolors.OKGREEN}OK {orig_key} in use, ingoring...{Bcolors.ENDC}")
        except KeyError:
            print(f"{Bcolors.FAIL}{orig_key} not found in config...deleting{Bcolors.ENDC}")
            redis.conn.delete(orig_key)   #delete here
            continue

if __name__ == '__main__':
    main()
