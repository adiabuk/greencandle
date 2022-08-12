#pylint: disable=no-member
"""
Add missing SL and TP to redis
"""
import sys
from greencandle.lib.redis_conn import Redis
from greencandle.lib import config



def main():
    """
    Force adding of SL and TP to redis for given pair
    """

    config.create_config()
    redis = Redis()
    pair = sys.argv[1]

    redis.update_on_entry(pair, 'stop_loss_perc', config.main.stop_loss_perc)
    redis.update_on_entry(pair, 'take_profit_perc', config.main.take_profit_perc)

if __name__ == '__main__':
    main()
