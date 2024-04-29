#!/usr/bin/env python
#pylint: disable=no-member,too-many-locals,broad-except

"""
intermediate check in higher timeframe to ensure
we don't open a trade against longterm trend
"""
import os
import time
import glob
import sys
from pathlib import Path
import setproctitle
from greencandle.lib import config
from greencandle.lib.redis_conn import Redis
from greencandle.lib.logger import get_logger, exception_catcher
from greencandle.lib.alerts import send_slack_message
from greencandle.lib.common import arg_decorator, get_tv_link
from greencandle.lib.auth import binance_auth

config.create_config()
INTERVAL = config.main.interval
NEW_INTERVAL = os.environ['INTERVAL'] if 'INTERVAL' in os.environ else ''
DIRECTION = config.main.trade_direction
LOGGER = get_logger(__name__)
PAIRS = config.main.pairs.split()
GET_EXCEPTIONS = exception_catcher((Exception))
TRIGGERED = {}

if sys.argv[-1] != "--help":
    CLIENT = binance_auth()
    ISOLATED = CLIENT.get_isolated_margin_pairs()
    CROSS = CLIENT.get_cross_margin_pairs()
    STORE_IN_DB = bool('STORE_IN_DB' in os.environ)
    CHECK_REDIS_PAIR = int(os.environ['CHECK_REDIS_PAIR']) if 'CHECK_REDIS_PAIR' in \
            os.environ else False
    ROUTER_FORWARD = bool('ROUTER_FORWARD' in os.environ)
    REDIS_FORWARD = [int(x) for x in os.environ['REDIS_FORWARD'].split(',')] if 'REDIS_FORWARD' \
            in os.environ else False

def analyse_loop():
    """
    Gather data from redis and analyze
    """
    LOGGER.debug("recently triggered: %s", str(TRIGGERED))

    Path('/var/local/greencandle').touch()
    while glob.glob(f'/var/run/{config.main.base_env}-data-{INTERVAL}-*'):
        LOGGER.info("waiting for initial data collection to complete for %s", INTERVAL)
        time.sleep(30)

    LOGGER.debug("start of current loop")
    redis = Redis()
    redis4=Redis(db=CHECK_REDIS_PAIR)

    pairs = [x.decode().split(':') for x in
                   redis4.conn.smembers(f'{NEW_INTERVAL}:{DIRECTION}')]
    del redis4

    for pair in pairs:
        analyse_pair(pair, redis)
    LOGGER.debug("end of current loop")
    del redis
    if CHECK_REDIS_PAIR:
        time.sleep(5)
    else:
        time.sleep(1)

def analyse_pair(pair, redis):
    """
    Analysis of individual pair
    """
    pair, reversal = pair

    LOGGER.debug("analysing pair: %s", pair)

    result = redis.get_rule_action(pair=pair, interval=INTERVAL)[0]

    redis3 = Redis(db=CHECK_REDIS_PAIR)
    redis3.conn.srem(f'{NEW_INTERVAL}:{DIRECTION}', f'{pair}:{reversal}')

    # swap direction if we don't match rule
    directions = ['long', 'short']
    if result.lower() == 'open':
        new_direction = config.main.trade_direction
    else:
        directions.remove(config.main.trade_direction)
        new_direction = directions[0]

    reversal = "reversal" if DIRECTION != new_direction else reversal
    LOGGER.info("adding %s to %s:%s set", pair, NEW_INTERVAL, new_direction)
    redis4 = Redis(db=REDIS_FORWARD[0])
    redis4.conn.sadd(f'{NEW_INTERVAL}:{new_direction}', f'{pair}:{reversal}')
    del redis4

    redis0 = Redis(db=0)
    items = redis0.get_items(pair, INTERVAL)
    data = redis0.get_item(f"{pair}:{INTERVAL}", items[-1]).decode()
    redis3 = Redis(db=3)
    raw_agg = redis3.conn.hgetall(f"{pair}:{INTERVAL}")
    agg = {k.decode():v.decode() for k,v in raw_agg.items()}

    send_slack_message("alerts", f"{get_tv_link(pair, NEW_INTERVAL)}:{NEW_INTERVAL} "
                                 f"{config.main.trade_direction} -> "
                                 f"{new_direction} ({reversal}) "
                                 f"Data: {data} Agg: {agg}",
                       emoji=True,
                       icon=f"{NEW_INTERVAL}-{new_direction}")
    LOGGER.info("trade alert: %s %s -> %s %s -> %s (%s)", pair, INTERVAL,NEW_INTERVAL, DIRECTION,
                new_direction, reversal)

@arg_decorator
def main():
    """
    Analyse data from redis from lower timeframe and ensure we are opening
    trade in correct trend.
    Required: CONFIG_ENV var and config:
    Env Vars:
      * CHECK_REDIS_PAIR
      * REDIS_FORWARD
      * INTERVAL (interval of previous and next containers, not current)

    Usage: analyse_direction
    """
    setproctitle.setproctitle(f"analyse_direction-{INTERVAL}")

    while True:
        analyse_loop()

if __name__ == "__main__":
    main()
