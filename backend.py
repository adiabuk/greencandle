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
import argcomplete
import setproctitle
import binance
from lib.mysql import Mysql
from lib.binance_common import get_dataframes
from lib.engine import Engine
from lib.config import get_config
from lib.logger import getLogger
from lib.redis_conn import Redis
from lib.order import buy, sell

LOGGER = getLogger(__name__)
PRICE_PER_TRADE = int(get_config("backend")["price_per_trade"])
MAX_TRADES = int(get_config("backend")["max_trades"])
INTERVAL = str(get_config("backend")["interval"])

def main():
    """ main function """
    setproctitle.setproctitle("greencandle-backend")
    parser = argparse.ArgumentParser()
    parser.add_argument("-g", "--graph", action="store_true", default=False)
    parser.add_argument("-j", "--json", action="store_true", default=False)
    parser.add_argument("-t", "--test", action="store_true", default=False)
    parser.add_argument("-p", "--pair")
    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    starttime = time.time()
    minutes = 4

    while True:
        try:
            loop(args)
        except KeyboardInterrupt:
            LOGGER.info("\nExiting on user command...")
            sys.exit(1)
        remaining_time = (minutes * 60.0) - ((time.time() - starttime) % 60.0)
        LOGGER.debug("Sleeping for %s seconds", remaining_time)
        time.sleep(remaining_time)

def loop(args):
    """
    Loop through collection cycle
    """

    LOGGER.debug("Starting new cycle")
    LOGGER.debug("Price per trade: %s", PRICE_PER_TRADE)
    LOGGER.debug("max trades: %s", MAX_TRADES)

    if args.pair:
        pairs = [args.pair]
    else:
        pairs = get_config("backend")["pairs"].split()
    prices = binance.prices()
    prices_trunk = {}
    for key, val in prices.items():
        if key in pairs:
            prices_trunk[key] = val
    dataframes = get_dataframes(pairs, interval=INTERVAL)

    engine = Engine(prices=prices_trunk, dataframes=dataframes, interval=INTERVAL)
    engine.get_data()
    dbase = Mysql(test=False, interval=INTERVAL)
    dbase.clean_stale()
    del dbase
    redis = Redis(interval=INTERVAL, test=False, db=0)
    buys = []
    sells = []
    for pair in pairs:
        investment = 20   #FIXME
        result, current_time, current_price = redis.get_change(pair=pair)
        LOGGER.debug("Changed items: %s %s %s", pair, result, current_time)
        if result == "buy":
            LOGGER.info("Items to buy")
            buys.append((pair, current_time, current_price))
        elif result == "sell":
            LOGGER.info("Items to sell")
            sells.append((pair, current_time, current_price))
    sell(sells, test_data=False, test_trade=False, interval=INTERVAL)
    buy(buys, test_data=False, test_trade=False, interval=INTERVAL)
    del redis

if __name__ == "__main__":
    main()
    LOGGER.debug("COMPLETE")
