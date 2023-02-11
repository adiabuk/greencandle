#!/usr/bin/env python
#pylint: disable=no-member

"""
Redis clear DB
"""

from greencandle.lib.redis_conn import Redis
from greencandle.lib.common import arg_decorator

@arg_decorator
def main():
    """
    Clear all Redis DB rows
    """

    for dbase in [0, 1, 2]:
        redis = Redis(db=dbase)
        redis.clear_all()


if __name__ == '__main__':
    main()
