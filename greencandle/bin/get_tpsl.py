#pylint: disable=no-member
"""
Retrieve SL and TP from redis
"""
import sys
from greencandle.lib.common import arg_decorator
from greencandle.lib.redis_conn import Redis
from greencandle.lib import config
from greencandle.lib.mysql import Mysql

@arg_decorator
def main():
    """
    Retrieve TP and SL from redis for given pair
    Usage: get_tpsl <pair>
    """

    config.create_config()
    dbase = Mysql()
    redis = Redis(db=2)
    pair = sys.argv[1]
    name = config.main.name
    direction = config.main.trade_diction

    if dbase.trade_in_context(pair, name, direction):
        take_profit = redis.get_on_entry(pair, 'take_profit_perc')
        stop_loss = redis.get_on_entry(pair, 'stop_loss_perc')
        print("TP: {}\nSL: {}".format(take_profit, stop_loss))
    else:
        print("No open trades in current context")

if __name__ == '__main__':
    main()
