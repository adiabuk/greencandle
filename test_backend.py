#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
"""
Run module with test data
"""

import argparse
import os
import pickle
from concurrent.futures import ThreadPoolExecutor
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
    parser.add_argument("-d", "--data_dir", required=True)

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
    serial_intervals = [args.interval] if args.interval else serial_intervals
    redis_db = {"15m":1, "5m":2, "3m":3, "1m":4}[parallel_interval]

    dbase = Mysql(test=True, interval=parallel_interval)
    dbase.delete_data()
    del dbase
    if args.serial:
        do_serial(pairs, serial_intervals, args.data_dir)
    else:
        do_parallel(pairs, parallel_interval, redis_db, args.data_dir)

def do_serial(pairs, intervals, data_dir):
    """
    Do test with serial data
    """
    #results = defaultdict(defaultdict)
    LOGGER.info("Performaing serial run")

    for pair in pairs:
        for interval in intervals:
            dbase = Mysql(test=True, interval=interval)
            dbase.delete_data()
            del dbase
            redis_db = {"15m":1, "5m":2, "3m":3, "1m":4}[interval]
            redis = Redis(interval=interval, test=True, db=redis_db)
            redis.clear_all()
            del redis



        for interval in intervals:
            with ThreadPoolExecutor(max_workers=len(intervals)) as pool:
                pool.submit(perform_data, pair, interval, data_dir)
    #filename = "./results.p"   #FIXME
    #pickle.dump(results, open(filename, "wb"))

def perform_data(pair, interval, data_dir):
    redis_db = {"15m":1, "5m":2, "3m":3, "1m":4}[interval]
    LOGGER.info("Serial run %s %s %s", pair, interval, redis_db)
    redis = Redis(interval=interval, test=True, db=redis_db)
    filename = "test_data/{0}/{1}_{2}.p".format(data_dir, pair, interval)
    if not os.path.exists(filename):
        LOGGER.critical("Data not found for %s %s", pair, interval)
        return
    with open(filename, "rb") as handle:
        dframe = pickle.load(handle)

    prices_trunk = {pair: "0"}
    for beg in range(len(dframe) - CHUNK_SIZE * 2):
        print("IN LOOP", interval, pair, beg, len(dframe), CHUNK_SIZE)
        sells = []
        buys = []
        end = beg + CHUNK_SIZE
        dataframe = dframe.copy()[beg: end]
        if len(dataframe) < 50:
            LOGGER.info("End of dataframe")
            break
        dataframes = {pair:dataframe}
        engine = Engine(prices=prices_trunk, dataframes=dataframes,
                        interval=interval, test=True, db=redis_db)
        engine.get_data()
        del engine
        result, current_time, current_price = redis.get_change(pair=pair)
        LOGGER.info("Changed items: %s %s %s", pair, result, current_time)
        if result == "buy":
            LOGGER.debug("Items to buy")
            buys.append((pair, current_time, current_price))
        elif result == "sell":
            LOGGER.debug("Items to sell")
            sells.append((pair, current_time, current_price))
        sell(sells, test_data=True, test_trade=True, interval=interval)
        buy(buys, test_data=True, test_trade=True, interval=interval)

    profit = get_recent_profit(True, interval=interval)
    #results[pair][interval] = profit[0]  #FIXME
    del redis
    LOGGER.info("AMROX4 %s %s %s", pair, interval, profit)

def do_parallel(pairs, interval, redis_db, data_dir):
    """
    Do test with parallel data
    """
    LOGGER.info("Performaing parallel run %s", interval)
    redis = Redis(interval=interval, test=True, db=redis_db)
    size = 1000 * {"15m": 1, "5m": 3, "3m": 5, "1m": 15}[interval]

    redis.clear_all()
    dframes = {}
    for pair in pairs:
        filename = "test_data/{0}/{1}_{2}.p".format(data_dir, pair, interval)
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
            result, _, _ = redis.get_change(pair=pair)
            LOGGER.info("Changed items: %s %s", result, pair)
            if result == "BUY":
                LOGGER.debug("Items to buy")
                buys.append(pair)
            if result == "SELL":
                LOGGER.debug("Items to sell")
                sells.append(pair)
        sell(sells, test_data=True, test_trade=True, interval=interval)
        buy(buys, test_data=True, test_trade=True, interval=interval)



    print(get_recent_profit(True, interval=interval))

if __name__ == "__main__":
    main()
