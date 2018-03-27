#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

"""
Run module with test data
"""

import argparse
import pickle
import argcomplete
import setproctitle
from lib.engine import Engine
from lib.common import make_float
from lib.logger import getLogger
from lib.redis_conn import Redis
from lib.config import get_config
from lib.mysql import mysql

LOGGER = getLogger(__name__)

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
    serial_intervals = get_config("test")["serial_intervals"].split()

    investment = 20
    dbase = mysql(test=True)
    dbase.delete_data()
    if args.serial:
        do_serial(pairs, serial_intervals, investment)
    else:
        do_parallel(pairs, parallel_interval, investment)



def do_serial(pairs, intervals, investment):
    """
    Do test with serial data
    """
    LOGGER.info("Performaing serial run")
    for pair in pairs:
        for interval in intervals:

            redis = Redis(interval=interval, test=True)
            filename = "test_data/{0}_{1}.p".format(pair, interval)
            with open(filename, "rb") as handle:
                dframe = pickle.load(handle)

            prices_trunk = {pair: "0"}
            chunk_size = 50
            redis.clear_all()
            for beg in range(len(dframe) - chunk_size * 2):
                end = beg + chunk_size
                dataframe = dframe.copy()[beg: end]
                if len(dataframe) < 50:
                    break
                dataframes = {pair:dataframe}
                engine = Engine(prices=prices_trunk, dataframes=dataframes,
                                interval=interval, test=True)
                data = engine.get_data()
                redis.get_change(pair=pair, investment=investment)

                del engine
                del data

def do_parallel(pairs, interval, investment):
    """
    Do test with parallel data
    """
    LOGGER.info("Performaing parallel run")
    redis = Redis(interval=interval, test=True)
    size = 1000
    chunk_size = 50

    redis.clear_all()
    dframes = {}
    for pair in pairs:
        filename = "test_data/{0}_{1}.p".format(pair, interval)
        with open(filename, "rb") as handle:
            dframes[pair] = pickle.load(handle)

    for beg in range(size - chunk_size * 2):
        dataframes = {}
        for pair in pairs:
            end = beg + chunk_size
            dataframe = dframes[pair][beg: end]
            prices_trunk = {pair: "0"}
            if len(dataframe) < 50:
                break
            dataframes.update({pair:dataframe})
            engine = Engine(prices=prices_trunk, dataframes=dataframes,
                            interval=interval, test=True)
            data = engine.get_data()
            redis.get_change(pair=pair, investment=investment)

            del engine
            del data


if __name__ == "__main__":
    main()
