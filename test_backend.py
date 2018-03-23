#!/usr/bin/env python

"""
Run module with test data
"""

import pickle
from lib.engine import Engine
from lib.common import make_float
from lib.logger import getLogger
from lib.redis_conn import Redis
from lib.config import get_config

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
    pairs = get_config("test")["pairs"].split()
    intervals = get_config("test")["intervals"].split()
    investment = 20

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
                data = ({pair:ohlc}, {pair:dataframe})
                engine = Engine(prices=prices_trunk, data=data, interval=interval, test=True)
                data = engine.get_data()
                redis.get_change(pair=pair, investment=investment)

                del engine
                del data

if __name__ == "__main__":
    main()
