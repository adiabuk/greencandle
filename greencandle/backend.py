#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
# pylint: disable=broad-except,no-member,too-many-locals,wrong-import-position

"""
Get ohlc (Open, High, Low, Close) values from given cryptos
and detect trends using candlestick patterns
"""

import argparse
import time
import sys
import re
from pathlib import Path
import argcomplete
import setproctitle

import binance
from str2bool import str2bool

from .lib import config
config.create_config(test=False)
from .lib.binance_common import get_dataframes
from .lib.engine import Engine
from .lib.logger import getLogger
from .lib.redis_conn import Redis
from .lib.order import Trade
from .lib.mysql import Mysql

LOGGER = getLogger(__name__, config.main.logging_level)

def main():
    """ main function """
    parser = argparse.ArgumentParser()
    parser.add_argument("-g", "--graph", action="store_true", default=False)
    parser.add_argument("-j", "--json", action="store_true", default=False)
    parser.add_argument("-t", "--test", action="store_true", default=False)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--use-api", action="store_true")
    group.add_argument("--use-redis", action="store_true")
    parser.add_argument("-i", "--interval")
    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    starttime = time.time()
    interval = args.interval if args.interval else str(config.main.interval)
    system = "api" if args.use_api else "redis"
    minutes = [int(s) for s in re.findall(r'(\d+)[mh]', interval)][0]
    drain = str2bool(config.main['drain_'+interval])
    drain_string = "(draining)" if drain else "(active)"
    setproctitle.setproctitle("greencandle-backend_{0}{1}".format(interval, drain_string))
    while True:
        try:
            loop(interval, args.test, system)
        except KeyboardInterrupt:
            LOGGER.warning("\nExiting on user command...")
            sys.exit(1)
        remaining_time = (minutes * 60.0) - ((time.time() - starttime) % 60.0)
        LOGGER.info("Sleeping for %s seconds", remaining_time)
        time.sleep(remaining_time)

def loop(interval, test, system):
    """
    Loop through collection cycle
    """
    main_indicators = config.main.indicators.split()
    main_pairs = config.main.pairs.split()
    dbase = Mysql(test=False, interval=interval)
    additional_pairs = dbase.get_trades()
    del dbase
    # get unique list of pairs in config,
    #and those currently in an active trade
    print(type(main_pairs))
    print(type(additional_pairs))
    pairs = list(set(main_pairs + additional_pairs))
    LOGGER.info("Pairs DB: %s", additional_pairs)
    LOGGER.info("Pairs in config: %s", main_pairs)
    LOGGER.info("Total unique pairs: %s", len(pairs))

    max_trades = int(config.main.max_trades)
    test_trade = test if test else str2bool(config.main.test_trade)

    LOGGER.info("Starting new cycle")
    Path('/var/run/greencandle').touch()
    LOGGER.debug("max trades: %s", max_trades)

    prices = binance.prices()
    prices_trunk = {}
    for key, val in prices.items():
        if key in pairs:
            prices_trunk[key] = val
    dataframes = get_dataframes(pairs, interval=interval)

    engine = Engine(prices=prices_trunk, dataframes=dataframes, interval=interval)
    if system == "redis":
        engine.get_data(localconfig=main_indicators)
        redis = Redis(interval=interval, test=False, db=0)
    else:
        pass
    buys = []
    sells = []
    for pair in pairs:
        ########TEST stategy############
        result, current_time, current_price = redis.get_action(pair=pair, interval=interval)
        LOGGER.info('In Strategy %s', result)
        if 'SELL' in result or 'BUY' in result:
            LOGGER.info('Strategy - Adding to redis')
            scheme = {}
            scheme["symbol"] = pair
            scheme["direction"] = result
            scheme['result'] = 0
            scheme['data'] = result
            scheme["event"] = "trigger"
            engine.add_scheme(scheme)
        ################################

        del engine

        if result == "BUY":
            LOGGER.debug("Items to buy")
            buys.append((pair, current_time, current_price))
        if result == "SELL":
            LOGGER.debug("Items to sell")
            sells.append((pair, current_time, current_price))
    trade = Trade(interval=interval, test_trade=test_trade, test_data=False)
    trade.sell(sells)
    trade.buy(buys)

    if system == "redis":
        del redis

if __name__ == "__main__":
    main()
    LOGGER.debug("COMPLETE")
