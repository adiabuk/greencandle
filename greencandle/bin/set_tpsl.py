#pylint: disable=no-member
"""
Set SL and TP in redis
"""
import sys
from greencandle.lib.common import arg_decorator
from greencandle.lib.redis_conn import Redis
from greencandle.lib import config


@arg_decorator
def main():
    """
    Force adding of SL and TP to redis for given pair
    Execute without values to use defaults in config
    Usage: set_tpsl <pair> [<take_profit> <stop_loss>]
    """

    config.create_config()
    redis = Redis()
    pair = sys.argv[1]
    if len(sys.argv) == 4:
        take_profit = sys.argv[2]
        stop_loss = sys.argv[3]
    else:
        take_profit = config.main.take_profit_perc
        stop_loss = config.main.stop_loss_perc

    redis.update_on_entry(pair, 'take_profit_perc', take_profit)
    redis.update_on_entry(pair, 'stop_loss_perc', stop_loss)

if __name__ == '__main__':
    main()
