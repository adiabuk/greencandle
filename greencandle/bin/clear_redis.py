#!/usr/bin/env python
#pylint: disable=no-member

"""
Redis clear DB
"""

import sys
from greencandle.lib.redis_conn import Redis
from greencandle.lib.common import arg_decorator
from greencandle.lib.logger import get_logger

@arg_decorator
def main():
    """
    Clear all Redis DB rows
    """

    logger = get_logger(__name__)
    dbases = [sys.argv[1]] if len(sys.argv) > 1 else [0, 1, 2, 3, 4]
    for dbase in dbases:
        logger.info("Clearing redis db %s", dbase)
        redis = Redis(db=dbase)
        redis.clear_all()

if __name__ == '__main__':
    main()
