#!/usr/bin/env python

import pickle
from backend import Events
from lib.common import make_float
from lib.logger import getLogger
from lib.redis_conn import Redis
from lib.config import get_config

logger = getLogger(__name__)

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
    pairs = get_config('test')['pairs'].split()
    intervals = get_config('test')['intervals'].split()

    redis = Redis()
    for pair in pairs:
        for interval in intervals:
            filename = "test_data/{0}_{1}.p".format(pair, interval)
            with open(filename, "rb") as handle:
                df = pickle.load(handle)

            prices_trunk = {pair: '0'}
            start = 50
            redis.clear_all()
            for i in range(1000):
                beg = i + start
                end = i  + start + start
                dataframe = df.copy()[beg: end]
                ohlc = make_data_tupple(dataframe)
                data = ({pair:ohlc}, {pair:dataframe})

                events = Events(prices=prices_trunk, data=data, interval=interval, test=True)
                data = events.get_data()
                redis.get_change(pair=pair, interval=interval)

                #insert_action_totals()
                #clean_stale()
                #sell(get_sell())
                #buy(get_buy())
                del data

if __name__ == '__main__':
    main()
