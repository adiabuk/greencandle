#pylint: disable=no-member,too-few-public-methods
"""
Cleanup redis db2 from unused keys
"""

import re
from greencandle.lib.redis_conn import Redis
from greencandle.lib.mysql import Mysql
from greencandle.lib.common import get_be_services, list_to_dict, arg_decorator
from greencandle.lib import config
from greencandle.lib.logger import get_logger

@arg_decorator
def main():
    """
    Cleanup redis db2 from unused keys
    Check open trades for matches and delete key if not found
    """

    logger = get_logger(__name__)
    config.create_config()
    dbase = Mysql()
    redis=Redis(db=2)
    open_trades = dbase.get_open_trades(name_filter='')
    keys = [x.decode() for x in redis.conn.keys()]

    short_dict = list_to_dict(get_be_services(config.main.base_env), reverse=True)
    for key in keys:
        orig_key = key
        try:
            pair, _, short = key.split(':')
            direction=short.split('-')[-1]
            long_name = re.sub(rf'-{direction}', '', short_dict[short])

            res = [i for i in open_trades if i[2]== pair and i[3]==long_name and i[5]==direction]
            if not res:
                logger.info("%s not used...deleting", orig_key)
                redis.conn.delete(orig_key)   #delete here
            else:
                logger.info("OK: %s in use, ingoring", orig_key)
        except KeyError:
            logger.info("%s not found in config...deleting", orig_key)
            redis.conn.delete(orig_key)   #delete here
            continue

if __name__ == '__main__':
    main()
