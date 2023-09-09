#pylint: disable=no-member
"""
Retrieve SL and TP from redis
"""
import sys
from greencandle.lib.common import arg_decorator
from greencandle.lib.redis_conn import Redis
from greencandle.lib.mysql import Mysql

@arg_decorator
def main():
    """
    Retrieve TP and SL from redis for given pair
    Usage: get_draw <pair> <name> <direction> up|down
    """

    dbase = Mysql()
    interval = sys.argv
    pair = sys.argv[1]
    name = sys.argv[2]
    direction = sys.argv[3]
    updown = sys.argv[4]

    redis = Redis(interval=interval, test_data=False, db=2)

    if updown == 'up':
        result = redis.get_drawup(pair, name=name, direction=direction)
    elif updown == 'down':
        result = redis.get_drawdown(pair, name=name, direction=direction)
    else:
        result = 'error'

    print(result)

if __name__ == '__main__':
    main()
