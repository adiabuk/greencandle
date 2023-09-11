#!/usr/bin/env python
#pylint: disable=no-member,global-statement,too-many-locals,broad-except

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
from greencandle.lib.common import arg_decorator
from greencandle.lib.auth import binance_auth

config.create_config()
INTERVAL = config.main.interval
NEW_INTERVAL = os.environ['INTERVAL']
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
    LOGGER.debug("Recently triggered: %s", str(TRIGGERED))

    Path('/var/local/greencandle').touch()
    while glob.glob(f'/var/run/{config.main.base_env}-data-{INTERVAL}-*'):
        LOGGER.info("Waiting for initial data collection to complete for %s", INTERVAL)
        time.sleep(30)

    LOGGER.debug("Start of current loop")
    redis = Redis()
    redis4=Redis(db=CHECK_REDIS_PAIR)
    pairs = [x.decode() for x in redis4.conn.smembers(f'{INTERVAL}:{DIRECTION}')]

    del redis4

    for pair in pairs:
        analyse_pair(pair, redis)
    LOGGER.debug("End of current loop")
    del redis
    if CHECK_REDIS_PAIR:
        time.sleep(5)
    else:
        time.sleep(1)

def rm_pair_from_redis(pair, dbase):
    """
    Remove pair from redis set
    """
    redis4 = Redis(db=dbase)
    redis4.conn.srem(f'{NEW_INTERVAL}:{DIRECTION}', pair)

def analyse_pair(pair, redis):
    """
    Analysis of individual pair
    """
    pair = pair.strip()

    LOGGER.debug("Analysing pair: %s", pair)

    result = redis.get_rule_action(pair=pair, interval=INTERVAL)[0]

    rm_pair_from_redis(pair, dbase=CHECK_REDIS_PAIR)

    # swap direction if we don't match rule
    directions = ['long', 'short']
    if result == 'open':
        new_direction = config.env.trade_direction
    else:
        directions.remove(config.env.trade_direction)
        new_direction = directions[0]

    forward_db = REDIS_FORWARD[0] if result == 'OPEN' else REDIS_FORWARD[1]
    LOGGER.info("Adding %s to %s:%s set", pair, INTERVAL, DIRECTION)
    redis4 = Redis(db=forward_db)
    redis4.conn.sadd(f'{INTERVAL}:{new_direction}', pair)
    del redis4

    send_slack_message("alerts", f"{pair} {config.env.trade_direction} -> {new_direction}")
    LOGGER.info("Trade alert: %s %s -> %s %s -> %s", pair, INTERVAL,NEW_INTERVAL, DIRECTION,
                new_direction)



@arg_decorator
def main():
    """
    Analyse data from redis from lower timeframe and ensure we are opening
    trade in correct trend.
    Required: CONFIG_ENV var and config:
    Env Vars:
      * VPN_IP
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
