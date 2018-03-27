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
    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    pairs = args.pairs if args.pairs else get_config("test")["pairs"].split()
    intervals = get_config("test")["intervals"].split()
    investment = 20
    dbase = mysql(test=True)
    dbase.delete_data()

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
                ohlc = make_data_tupple(dataframe)
                dataframes =  {pair:dataframe}
                engine = Engine(prices=prices_trunk, dataframes=dataframes, interval=interval, test=True)
                data = engine.get_data()
                redis.get_change(pair=pair, investment=investment)

                del engine
                del data

if __name__ == "__main__":
    main()
