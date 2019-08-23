#!/usr/bin/env python
#pylint: disable=no-member, wrong-import-position
# PYTHON_ARGCOMPLETE_OK
"""
Run module with test data
"""

import argparse
import os
import sys
import pickle
from concurrent.futures import ThreadPoolExecutor
import argcomplete
import setproctitle

from .lib import config
# config is required before loading other modules as it is global
config.create_config(test=True)

from .lib.engine import Engine
from .lib.common import make_float
from .lib.redis_conn import Redis
from .lib.mysql import Mysql
from .lib.profit import get_recent_profit
from .lib.order import Trade
from .lib.logger import getLogger, get_decorator

LOGGER = getLogger(__name__, config.main.logging_level)
CHUNK_SIZE = 200
GET_EXCEPTIONS = get_decorator((Exception))

def main():
    """
    Run test for all pairs and intervals defined in config
    """
    setproctitle.setproctitle("greencandle-test")
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--interval")
    parser.add_argument("-p", "--pairs", nargs='+', required=False, default=[])
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-s", "--serial", default=False, action="store_true")
    group.add_argument("-a", "--parallel", default=True, action="store_true")
    parser.add_argument("-d", "--data_dir", required=True)

    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    pairs = args.pairs if args.pairs else config.main.pairs.split()
    parallel_interval = config.main.parallel_interval.split()[0]
    parallel_interval = args.interval if args.interval else parallel_interval
    main_indicators = config.main.indicators.split()
    serial_intervals = [args.interval]
    redis_db = {"4h":1, "2h":1, "1h":1, "30m":1, "15m":1, "5m":2, "3m":3, "1m":4}[parallel_interval]

    dbase = Mysql(test=True, interval=parallel_interval)
    dbase.delete_data()
    del dbase
    if args.serial:
        do_serial(pairs, serial_intervals, args.data_dir, main_indicators)
    else:
        do_parallel(pairs, parallel_interval, redis_db, args.data_dir, main_indicators)

@GET_EXCEPTIONS
def do_serial(pairs, intervals, data_dir, indicators):
    """
    Do test with serial data
    """
    LOGGER.info("Performaing serial run")

    for pair in pairs:
        for interval in intervals:
            dbase = Mysql(test=True, interval=interval)
            dbase.delete_data()
            del dbase
            redis_db = {"4h":1, "2h":1, "1h":1, "30m":1, "15m":1, "5m":2, "3m":3, "1m":4}[interval]
            redis = Redis(interval=interval, test=True, db=redis_db)
            redis.clear_all()
            del redis

        for interval in intervals:
            with ThreadPoolExecutor(max_workers=len(intervals)) as pool:
                pool.submit(perform_data, pair, interval, data_dir, indicators)

@GET_EXCEPTIONS
def perform_data(pair, interval, data_dir, indicators):
    redis_db = {"4h":1, "2h":1, "1h":1, "30m":1, "15m":1, "5m":2, "3m":3, "1m":4}[interval]
    LOGGER.info("Serial run %s %s %s", pair, interval, redis_db)
    redis = Redis(interval=interval, test=True, db=redis_db)
    filename = "{0}/{1}_{2}.p".format(data_dir, pair, interval)
    if not os.path.exists(filename):
        LOGGER.critical("Filename:%s not found for %s %s", filename, pair, interval)
        return
    with open(filename, "rb") as handle:
        dframe = pickle.load(handle)

    prices_trunk = {pair: "0"}
    for beg in range(len(dframe) - CHUNK_SIZE):
        LOGGER.info("IN LOOP %s ", beg)
        trade = Trade(interval=interval, test=True, test_trade=True, test_data=True)

        sells = []
        buys = []
        end = beg + CHUNK_SIZE
        LOGGER.info("chunk: %s, %s", beg, end)
        dataframe = dframe.copy()[beg: end]
        LOGGER.info("current date: %s, %s", dataframe.iloc[-1].closeTime, len(dataframe))
        if len(dataframe) < CHUNK_SIZE:
            LOGGER.info("End of dataframe")
            break
        dataframes = {pair:dataframe}
        engine = Engine(prices=prices_trunk, dataframes=dataframes,
                        interval=interval, test=True, db=redis_db)
        engine.get_data(localconfig=indicators)

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
            buys.append((pair, current_time, current_price))
            LOGGER.debug("Items to buy: %s", buys)
            trade.buy(buys)
        elif result == "SELL":
            sells.append((pair, current_time, current_price))
            LOGGER.debug("Items to sell: %s", sells)
            trade.sell(sells)

    del redis
    LOGGER.info("Selling remaining items")
    sells = []
    sells.append((pair, current_time, current_price))
    trade.sell(sells)
    profit = get_recent_profit(True, interval=interval)

def do_parallel(pairs, interval, redis_db, data_dir, indicators):
    """
    Do test with parallel data
    """
    LOGGER.info("Performaing parallel run %s", interval)
    redis = Redis(interval=interval, test=True, db=redis_db)
    size = 1000 * {"1h":0.25, "30m":0.5, "15m": 1, "5m": 3, "3m": 5, "1m": 15}[interval]

    trade = Trade(interval=interval, test=True, test_trade=True, test_data=True)
    redis.clear_all()
    dframes = {}
    for pair in pairs:
        filename = "/{0}/{1}_{2}.p".format(data_dir, pair, interval)
        if not os.path.exists(filename):
            LOGGER.critical("Cannot file file: %s", filename)
            continue
        with open(filename, "rb") as handle:
            dframes[pair] = pickle.load(handle)

    for beg in range(int(size) - CHUNK_SIZE * 2):
        dataframes = {}
        buys = []
        sells = []
        for pair in pairs:
            end = beg + CHUNK_SIZE
            dataframe = dframes[pair][beg: end]
            prices_trunk = {pair: "0"}
            if len(dataframe) < CHUNK_SIZE:
                break
            dataframes.update({pair:dataframe})
            engine = Engine(prices=prices_trunk, dataframes=dataframes,
                            interval=interval, test=True, db=redis_db)
            engine.get_data(localconfig=indicators)

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
        trade.sell(sells)
        trade.buy(buys)

    print(get_recent_profit(True, interval=interval))

if __name__ == "__main__":

    print(config)
    sys.exit()
    main()
