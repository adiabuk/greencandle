#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
"""
Run module with test data
"""

import argparse
import os
import pickle
import argcomplete
import setproctitle
from lib.engine import Engine
from lib.common import make_float
from lib.logger import getLogger
from lib.redis_conn import Redis
from lib.config import get_config
from lib.mysql import Mysql
from lib.profit import get_recent_profit
from lib.order import buy, sell

LOGGER = getLogger(__name__)
CHUNK_SIZE = 50

def make_data_tupple(dataframe):
    """
    Transform dataframe to tupple of of floats
    """
    ohlc = (make_float(dataframe.open),
            make_float(dataframe.high),
            make_float(dataframe.low),
            make_float(dataframe.close))
    return ohlc

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

    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    if args.serial:
        pair_string = "serial_pairs"
    else:
        pair_string = "parallel_pairs"
    pairs = args.pairs if args.pairs else get_config("test")[pair_string].split()
    parallel_interval = get_config("test")["parallel_interval"].split()[0]
    parallel_interval = args.interval if args.interval else parallel_interval
    serial_intervals = get_config("test")["serial_intervals"].split()
    redis_db = {"15m":1, "5m":2, "3m":3, "1m":4}[parallel_interval]

    investment = 20
    dbase = Mysql(test=True, interval=parallel_interval)  # FIXME: for serial
    dbase.delete_data()
    if args.serial:
        do_serial(pairs, serial_intervals, investment)
    else:
        do_parallel(pairs, parallel_interval, investment, redis_db)

def do_serial(pairs, intervals, investment):
    """
    Do test with serial data
    """

    LOGGER.info("Performaing serial run")
    for pair in pairs:
        for interval in intervals:
            redis_db = {"15m":1, "5m":2, "3m":3, "1m":4}[interval]
            LOGGER.debug("Serial run %s %s %s", pair, interval, redis_db)
            dbase = Mysql(test=True, interval=interval)
            dbase.delete_data()
            redis = Redis(interval=interval, test=True, db=redis_db)
            redis.clear_all()
            filename = "test_data/{0}_{1}.p".format(pair, interval)
            if not os.path.exists(filename):
                continue
            with open(filename, "rb") as handle:
                dframe = pickle.load(handle)

            prices_trunk = {pair: "0"}
            for beg in range(len(dframe) - CHUNK_SIZE * 2):
                sells = []
                buys = []
                end = beg + CHUNK_SIZE
                dataframe = dframe.copy()[beg: end]
                if len(dataframe) < 50:
                    break
                dataframes = {pair:dataframe}
                engine = Engine(prices=prices_trunk, dataframes=dataframes,
                                interval=interval, test=True, db=redis_db)
                engine.get_data()
                buy_item, sell_item = redis.get_change(pair=pair, investment=investment)
                LOGGER.debug("Changed items: %s %s", buy_item, sell_item)
                if buy_item:
                    LOGGER.info("Items to buy")
                    buys.append(buy_item)
                if sell_item:
                    LOGGER.info("Items to sell")
                    sells.append(sell_item)
                sell(sells)
                buy(buys)

                del engine
            profit = get_recent_profit(True, interval=interval)
            LOGGER.debug("AMROX4 %s %s %s", pair, interval, profit)

def do_parallel(pairs, interval, investment, redis_db=1):
    """
    Do test with parallel data
    """
    LOGGER.info("Performaing parallel run %s", interval)
    redis = Redis(interval=interval, test=True, db=redis_db)
    size = 1000 * {"15m": 1, "5m": 3, "3m": 5, "1m": 15}[interval]

    redis.clear_all()
    dframes = {}
    for pair in pairs:
        filename = "test_data/{0}_{1}.p".format(pair, interval)
        if not os.path.exists(filename):
            continue
        with open(filename, "rb") as handle:
            dframes[pair] = pickle.load(handle)

    for beg in range(size - CHUNK_SIZE * 2):
        dataframes = {}
        buys = []
        sells = []
        for pair in pairs:
            end = beg + CHUNK_SIZE
            dataframe = dframes[pair][beg: end]
            prices_trunk = {pair: "0"}
            if len(dataframe) < 50:
                break
            dataframes.update({pair:dataframe})
            engine = Engine(prices=prices_trunk, dataframes=dataframes,
                            interval=interval, test=True, db=redis_db)
            engine.get_data()
            del engine
            buy_item, sell_item = redis.get_change(pair=pair, investment=investment)
            LOGGER.debug("Changed items: %s %s", buy_item, sell_item)
            if buy_item:
                LOGGER.info("Items to buy")
                buys.append(buy_item)
            if sell_item:
                LOGGER.info("Items to sell")
                sells.append(sell_item)
        sell(sells)
        buy(buys)



    print(get_recent_profit(True, interval=interval))

if __name__ == "__main__":
    main()
