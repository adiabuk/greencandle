#!/usr/bin/env python
"""
Add example trigger rules to db7 redis for displaying in UI
"""

import time
from greencandle.lib.redis_conn import Redis
from greencandle.lib.common import arg_decorator

@arg_decorator
def main():
    """
    Prompt for rule and title and store details in db7 redis
    """
    redis=Redis(db=7)

    key = int(time.time())
    title = input("input title: > ")
    rule = input("input rule: > ")

    contents = str([title, rule])

    redis.conn.set(key, contents)

if __name__ == '__main__':
    main()
