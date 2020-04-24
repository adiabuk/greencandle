# pylint: disable=no-member

"""
Perform run for test & prod
"""

import os
import time
import pickle
import gzip
from concurrent.futures import ThreadPoolExecutor
from glob import glob
import binance
from .engine import Engine
from .redis_conn import Redis
from .mysql import Mysql
from .profit import get_recent_profit
from .order import Trade
from .binance_common import get_dataframes
from .logger import get_logger, get_decorator
from .common import perc_diff
from . import config
LOGGER = get_logger(__name__)
CHUNK_SIZE = int(config.main.no_of_klines)
GET_EXCEPTIONS = get_decorator((Exception))

@GET_EXCEPTIONS
def serial_test(pairs, intervals, data_dir, indicators):
    """
    Do test with serial data
    """
    LOGGER.debug("Performaing serial run")

    for pair in pairs:
        for interval in intervals:
            dbase = Mysql(test=True, interval=interval)
            dbase.delete_data()
            del dbase
            redis = Redis(interval=interval, test=True, db=0)
            redis.clear_all()
            del redis

        for interval in intervals:
            with ThreadPoolExecutor(max_workers=len(intervals)) as pool:
                pool.submit(perform_data, pair, interval, data_dir, indicators)

def update_minprice(pair, buy_time, current_price, interval):
    """
    bla bla bla
    """
    redis = Redis(interval=interval, test=True, db=1)

    min_price = redis.get_item(pair, current_price)

    if (min_price and current_price < float(min_price)) or not min_price:
        data = {"buy_time": buy_time, "current_price": current_price}
        redis.redis_conn(pair, interval, data, buy_time)
    del redis

def get_drawdown():
    """
    bla bla bla
    """
    drawdown = perc_diff(buy_price, min_price)
    save_to_db
    remove_min_price
    dbase = Mysql(test=True, interval=interval)

@GET_EXCEPTIONS
def perform_data(pair, interval, data_dir, indicators):
    """Serial test loop"""
    LOGGER.debug("Serial run %s %s", pair, interval)
    redis = Redis(interval=interval, test=True, db=0)

    filename = glob("{0}/{1}_{2}.p*".format(data_dir, pair, interval))[0]
    if not os.path.exists(filename):
        LOGGER.critical("Filename:%s not found for %s %s", filename, pair, interval)
        return
    if filename.endswith("gz"):
        handle = gzip.open(filename, "rb")
    else:
        handle = open(filename, "rb")
    dframe = pickle.load(handle)
    handle.close()

    prices_trunk = {pair: "0"}
    for beg in range(len(dframe) - CHUNK_SIZE):
        LOGGER.debug("IN LOOP %s ", beg)
        trade = Trade(interval=interval, test_trade=True, test_data=True)

        sells = []
        buys = []
        end = beg + CHUNK_SIZE
        LOGGER.debug("chunk: %s, %s", beg, end)
        dataframe = dframe.copy()[beg: end]

        current_time = time.strftime("%Y-%m-%d %H:%M:%S",
                                     time.gmtime(int(dataframe.iloc[-1].closeTime)/1000))
        LOGGER.debug("current date: %s", current_time)
        if len(dataframe) < CHUNK_SIZE:
            LOGGER.debug("End of dataframe")
            break
        dataframes = {pair:dataframe}
        engine = Engine(prices=prices_trunk, dataframes=dataframes,
                        interval=interval, test=True, redis=redis)
        engine.get_data(localconfig=indicators)

        result, current_time, current_price, _ = redis.get_action(pair=pair, interval=interval)
        del engine

        if result == "BUY":
            buys.append((pair, current_time, current_price))
            LOGGER.debug("Items to buy: %s", buys)
            trade.buy(buys)
            update_minprice(pair, current_time, current_price, interval)
            # add current_price
        elif result == "SELL":
            sells.append((pair, current_time, current_price))
            LOGGER.debug("Items to sell: %s", sells)
            trade.sell(sells)
            # update price
        # elif still in trade
            # update price

    del redis
    LOGGER.info("Selling remaining items")
    sells = []
    sells.append((pair, current_time, current_price))
    trade.sell(sells)

def parallel_test(pairs, interval, data_dir, indicators):
    """
    Do test with parallel data
    """
    LOGGER.info("Performaing parallel run %s", interval)
    redis = Redis(interval=interval, test=True, db=0)
    redis.clear_all()
    dbase = Mysql(test=True, interval=interval)
    dbase.delete_data()
    del dbase

    trade = Trade(interval=interval, test_trade=True, test_data=True)
    dframes = {}
    sizes = []
    for pair in pairs:
        filename = glob("/{0}/{1}_{2}.p*".format(data_dir, pair, interval))[0]
        if not os.path.exists(filename):
            LOGGER.critical("Cannot find file: %s", filename)
            continue
        if filename.endswith("gz"):
            handle = gzip.open(filename, "rb")
        else:
            handle = open(filename, "rb")

        dframes[pair] = pickle.load(handle)
        sizes.append(len(dframes[pair]))
        LOGGER.info("%s dataframe size: %s", pair, len(dframes[pair]))
        handle.close()

    LOGGER.critical(dframes.keys())
    for beg in range(max(sizes) - CHUNK_SIZE):
        end = beg + CHUNK_SIZE
        dataframes = {}
        buys = []
        sells = []
        for pair in pairs:
            LOGGER.info("Current loop: %s to %s pair:%s", beg, end, pair)
            dataframe = dframes[pair][beg: end]
            prices_trunk = {pair: "0"}
            if len(dataframe) < CHUNK_SIZE:
                break
            dataframes.update({pair:dataframe})
            engine = Engine(prices=prices_trunk, dataframes=dataframes,
                            interval=interval, test=True, redis=redis)
            engine.get_data(localconfig=indicators)

            result, current_time, current_price, _ = redis.get_action(pair=pair, interval=interval)
            LOGGER.info('In Strategy %s', result)
            del engine

            if result == "BUY":
                LOGGER.debug("Items to buy")
                buys.append((pair, current_time, current_price))
            if result == "SELL":
                LOGGER.debug("Items to sell")
                sells.append((pair, current_time, current_price))
        trade.sell(sells, drawdown=drawdown)
        trade.buy(buys)

    print(get_recent_profit(True, interval))

def prod_int_check(interval, test):
    """Check price between candles for slippage below stoploss"""
    prices = binance.prices()
    dbase = Mysql(test=False, interval=interval)
    current_trades = dbase.get_trades()
    redis = Redis(interval=interval, test=False, db=0)
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    sells = []
    for trade in current_trades:
        pair = trade[0]
        buy_price = dbase.get_trade_value(pair)[0][0]
        result, current_time, current_price = redis.get_intermittant(pair, buy_price=buy_price,
                                                                     current_price=prices[pair])
        buy_price = dbase.get_trade_value(pair)[0][0]
        LOGGER.debug("%s int check result: %s Buy:%s Current:%s Time:%s", pair, result, buy_price,
                     current_price, current_time)
        if result == "SELL":
            LOGGER.debug("Items to sell")
            sells.append((pair, current_time, current_price))

    trade = Trade(interval=interval, test_trade=test, test_data=False)
    trade.sell(sells)
    del redis
    del dbase

def prod_initial(interval, test=False):
    """
    Initial prod run - back-fetching data for tech analysis.
    """
    prices = binance.prices()
    prices_trunk = {}
    pairs = config.main.pairs.split()

    for key, val in prices.items():
        if key in pairs:
            prices_trunk[key] = val

    redis = Redis(interval=interval, test=test)
    main_indicators = config.main.indicators.split()
    dataframes = get_dataframes(pairs, interval=interval)
    engine = Engine(prices=prices_trunk, dataframes=dataframes, interval=interval, test=test,
                    redis=redis)
    engine.get_data(localconfig=main_indicators, first_run=True)
    del redis

def prod_loop(interval, test_trade):
    """
    Loop through collection cycle (PROD)
    """
    main_indicators = config.main.indicators.split()
    pairs = config.main.pairs.split()

    LOGGER.debug("Performaing prod loop")
    LOGGER.info("Pairs in config: %s", pairs)
    LOGGER.info("Total unique pairs: %s", len(pairs))

    max_trades = int(config.main.max_trades)

    LOGGER.info("Starting new cycle")
    LOGGER.debug("max trades: %s", max_trades)

    prices = binance.prices()
    prices_trunk = {}
    for key, val in prices.items():
        if key in pairs:
            prices_trunk[key] = val
    dataframes = get_dataframes(pairs, interval=interval)

    redis = Redis(interval=interval, test=False)
    engine = Engine(prices=prices_trunk, dataframes=dataframes, interval=interval, redis=redis)
    engine.get_data(localconfig=main_indicators, first_run=False)
    buys = []
    sells = []
    for pair in pairs:
        result, current_time, current_price, _ = redis.get_action(pair=pair, interval=interval)

        if result == "BUY":
            LOGGER.debug("Items to buy")
            buys.append((pair, current_time, current_price))
        if result == "SELL":
            LOGGER.debug("Items to sell")
            sells.append((pair, current_time, current_price))
    trade = Trade(interval=interval, test_trade=test_trade, test_data=False)
    trade.sell(sells)
    trade.buy(buys)
    del engine
    del redis
