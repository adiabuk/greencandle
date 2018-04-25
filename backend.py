#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
# pylint: disable=broad-except,c-extension-no-member

"""
Get ohlc (Open, High, Low, Close) values from given cryptos
and detect trends using candlestick patterns
"""

import argparse
import time
import sys
import re
import argcomplete
from str2bool import str2bool
import setproctitle

import binance
from lib.binance_common import get_dataframes
from lib.engine import Engine
from lib.config import get_config
from lib.logger import getLogger
from lib.redis_conn import Redis
from lib.order import buy, sell

LOGGER = getLogger(__name__)


def main():
    """ main function """
    parser = argparse.ArgumentParser()
    parser.add_argument("-g", "--graph", action="store_true", default=False)
    parser.add_argument("-j", "--json", action="store_true", default=False)
    parser.add_argument("-t", "--test", action="store_true", default=False)
    parser.add_argument("-i", "--interval")
    parser.add_argument("-p", "--pair")
    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    starttime = time.time()
    interval = args.interval if args.interval else str(get_config("backend")["interval"])
    pairs = [args.pair] if args.pair else get_config("backend")["pairs"].split()
    minutes = [int(s) for s in re.findall(r'(\d+)m', interval)][0]
    drain = str2bool(get_config("backend")["drain_" + interval])
    drain_string = "(draining)" if drain else ""
    setproctitle.setproctitle("greencandle-backend_{0}{1}".format(interval, drain_string))

    while True:
        try:
            loop(pairs, interval)
        except KeyboardInterrupt:
            LOGGER.critical("\nExiting on user command...")
            sys.exit(1)
        remaining_time = (minutes * 60.0) - ((time.time() - starttime) % 60.0)
        LOGGER.info("Sleeping for %s seconds", remaining_time)
        time.sleep(remaining_time)

def loop(pairs, interval):
    """
    Loop through collection cycle
    """

    max_trades = int(get_config("backend")["max_trades"])
    test_trade = str2bool(get_config("backend")["test_trade"])
    LOGGER.info("Starting new cycle")
    LOGGER.debug("max trades: %s", max_trades)

    prices = binance.prices()
    prices_trunk = {}
    for key, val in prices.items():
        if key in pairs:
            prices_trunk[key] = val
    dataframes = get_dataframes(pairs, interval=interval)

    engine = Engine(prices=prices_trunk, dataframes=dataframes, interval=interval)
    engine.get_data()
    redis = Redis(interval=interval, test=False, db=0)
    buys = []
    sells = []
    for pair in pairs:
        result, current_time, current_price = redis.get_change(pair=pair)
        if result == "buy":
            LOGGER.debug("Items to buy")
            buys.append((pair, current_time, current_price))
        elif result == "sell":
            LOGGER.info("Items to sell")
            sells.append((pair, current_time, current_price))
    LOGGER.info("Items to sell: %s", sells)
    LOGGER.info("Items to buy: %s", buys)
    sell(sells, test_data=False, test_trade=test_trade, interval=interval)
    buy(buys, test_data=False, test_trade=test_trade, interval=interval)
    del redis

if __name__ == "__main__":
    main()
    LOGGER.debug("COMPLETE")
