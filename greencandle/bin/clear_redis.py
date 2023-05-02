#!/usr/bin/env python
#pylint: disable=no-member

"""
Redis clear DB
"""

import sys
from greencandle.lib.redis_conn import Redis
from greencandle.lib.common import arg_decorator

@arg_decorator
def main():
    """
    Clear all Redis DB rows
    """
    dbases = [sys.argv[1]] if len(sys.argv) > 1 else [0, 1, 2]
    for dbase in dbases:
        print("Clearing redis db {}".format(dbase))
        redis = Redis(db=dbase)
        redis.clear_all()


if __name__ == '__main__':
    main()
