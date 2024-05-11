#pylint: disable=no-member
"""
Set SL and TP in redis
"""
import sys
from greencandle.lib.common import arg_decorator
from greencandle.lib.redis_conn import Redis
from greencandle.lib import config
from greencandle.lib.mysql import Mysql


@arg_decorator
def main():
    """
    Force adding of SL and TP to redis for given pair
    Execute without values to use defaults in config
    Usage: set_tpsl <pair> <take_profit> <stop_loss> [force]
    """

    config.create_config()
    redis = Redis(db=2)
    pair = sys.argv[1]
    dbase = Mysql()
    name = config.main.name
    direction = config.main.trade_direction

    if dbase.trade_in_context(pair, name, direction) or 'force' in sys.argv:
        if len(sys.argv) >= 4:
            take_profit = sys.argv[2]
            stop_loss = sys.argv[3]
        else:
            take_profit = config.main.take_profit_perc
            stop_loss = config.main.stop_loss_perc

        redis.update_on_entry(pair, 'take_profit_perc', take_profit)
        redis.update_on_entry(pair, 'stop_loss_perc', stop_loss)
    else:
        print("No open trades in current context")

if __name__ == '__main__':
    main()
