#pylint: disable=no-member, logging-not-lazy

"""
Perform run for test & prod
"""

import os
import sys
import time
import pickle
import gzip
from concurrent.futures import ThreadPoolExecutor
from glob import glob
from binance import binance
from .engine import Engine
from .redis_conn import Redis
from .mysql import Mysql
from .profit import get_recent_profit
from .order import Trade
from .binance_common import get_dataframes
from .logger import get_logger, get_decorator
from . import config
LOGGER = get_logger(__name__)
CHUNK_SIZE = int(config.main.no_of_klines)
GET_EXCEPTIONS = get_decorator((Exception))
PAIRS = config.main.pairs.split()
MAIN_INDICATORS = config.main.indicators.split()

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
            redis = Redis(interval=interval, test=True, test_data=True)
            redis.clear_all()
            del redis

        for interval in intervals:
            with ThreadPoolExecutor(max_workers=len(intervals)) as pool:
                pool.submit(perform_data, pair, interval, data_dir, indicators)

@GET_EXCEPTIONS
def perform_data(pair, interval, data_dir, indicators):
    """Serial test loop"""
    LOGGER.debug("Serial run %s %s" % (pair, interval))
    redis = Redis(interval=interval, test=True, test_data=True)
    try:
        filename = glob("{0}/{1}_{2}.p*".format(data_dir, pair, interval))[0]
    except IndexError:
        print("File not found: {0}/{1}_{2}.p*".format(data_dir, pair, interval))
        sys.exit(1)
    if not os.path.exists(filename):
        LOGGER.critical("Filename:%s not found for %s %s" % (filename, pair, interval))
        return
    if filename.endswith("gz"):
        handle = gzip.open(filename, "rb")
    else:
        handle = open(filename, "rb")
    dframe = pickle.load(handle)
    handle.close()

    dbase = Mysql(test=True, interval=interval)
    prices_trunk = {pair: "0"}
    for beg in range(len(dframe) - CHUNK_SIZE):
        LOGGER.debug("IN LOOP %s " % beg)
        trade = Trade(interval=interval, test_trade=True, test_data=True)

        sells = []
        buys = []
        end = beg + CHUNK_SIZE
        LOGGER.debug("chunk: %s, %s" % (beg, end))
        dataframe = dframe.copy()[beg: end]

        current_ctime = int(dataframe.iloc[-1].closeTime)/1000
        current_time = time.strftime("%Y-%m-%d %H:%M:%S",
                                     time.gmtime(current_ctime))
        LOGGER.debug("current date: %s" %  current_time)

        if len(dataframe) < CHUNK_SIZE:
            LOGGER.debug("End of dataframe")
            break
        dataframes = {pair:dataframe}
        engine = Engine(prices=prices_trunk, dataframes=dataframes,
                        interval=interval, test=True, redis=redis)
        engine.get_data(localconfig=indicators)

        result, event, current_time, current_price, _ = redis.get_action(pair=pair,
                                                                         interval=interval)
        del engine
        current_trade = dbase.get_trade_value(pair)
        current_candle = dataframes[pair].iloc[-1]
        redis.update_drawdown(pair, current_candle)
        redis.update_drawup(pair, current_candle)

        if result == "OPEN":
            redis.update_drawdown(pair, current_candle, event='open')
            redis.update_drawup(pair, current_candle, event='open')
            buys.append((pair, current_time, current_price, event))
            LOGGER.debug("Items to buy: %s" % buys)
            trade.open_trade(buys)

        elif result == "CLOSE":
            sells.append((pair, current_time, current_price, event))
            LOGGER.debug("Items to sell: %s" % sells)
            drawdown = redis.get_drawdown(pair)
            drawup = redis.get_drawup(pair)['perc']
            redis.rm_drawup(pair)
            redis.rm_drawdown(pair)
            trade.close_trade(sells, drawdowns={pair:drawdown}, drawups={pair:drawup})

    LOGGER.info("Selling remaining item")
    sells = []
    if current_trade:
        sells.append((pair, current_time, current_price, event))
        current_candle = dataframes[pair].iloc[-1]

        redis.update_drawdown(pair, current_candle)
        redis.update_drawup(pair, current_candle)

        drawdown = redis.get_drawdown(pair)
        drawup = redis.get_drawup(pair)['perc']
        redis.rm_drawup(pair)
        redis.rm_drawdown(pair)

        trade.close_trade(sells, drawdowns={pair:drawdown}, drawups={pair:drawup})

    del redis
    del dbase

def parallel_test(pairs, interval, data_dir, indicators):
    """
    Do test with parallel data
    """
    LOGGER.info("Performaing parallel run %s" % interval)
    redis = Redis(interval=interval, test=True, test_data=True)
    redis.clear_all()
    dbase = Mysql(test=True, interval=interval)
    dbase.delete_data()
    del dbase
    trade = Trade(interval=interval, test_trade=True, test_data=True)
    dframes = {}
    sizes = []
    for pair in pairs:
        try:
            filename = glob("/{0}/{1}_{2}.p*".format(data_dir, pair, interval))[0]
        except IndexError:
            print("File not found: {0}/{1}_{2}.p*".format(data_dir, pair, interval))
            sys.exit(1)
        if not os.path.exists(filename):
            LOGGER.critical("Cannot find file: %s" % filename)
            continue
        if filename.endswith("gz"):
            handle = gzip.open(filename, "rb")
        else:
            handle = open(filename, "rb")

        dframes[pair] = pickle.load(handle)
        sizes.append(len(dframes[pair]))
        LOGGER.info("%s dataframe size: %s" % (pair, len(dframes[pair])))
        handle.close()

    for beg in range(max(sizes) - CHUNK_SIZE):
        end = beg + CHUNK_SIZE
        dataframes = {}
        buys = []
        sells = []
        drawdowns = {}
        drawups = {}
        for pair in pairs:
            LOGGER.info("Current loop: %s to %s pair:%s" % (beg, end, pair))
            dataframe = dframes[pair][beg: end]
            prices_trunk = {pair: "0"}
            if len(dataframe) < CHUNK_SIZE:
                break
            dataframes.update({pair:dataframe})
            engine = Engine(prices=prices_trunk, dataframes=dataframes,
                            interval=interval, test=True, redis=redis)
            engine.get_data(localconfig=indicators)

            result, event, current_time, current_price, _ = redis.get_action(pair=pair,
                                                                             interval=interval)
            current_candle = dataframe.iloc[-1]
            redis.update_drawdown(pair, current_candle)
            redis.update_drawup(pair, current_candle)

            LOGGER.info('In Strategy %s' % result)
            del engine

            if result == "OPEN":
                LOGGER.debug("Items to buy")
                redis.update_drawdown(pair, current_candle, event='open')
                redis.update_drawup(pair, current_candle, event='open')
                buys.append((pair, current_time, current_price, event))
            if result == "CLOSE":
                LOGGER.debug("Items to sell")
                drawdowns[pair] = redis.get_drawdown(pair)
                drawups[pair] = redis.get_drawup(pair)['perc']
                sells.append((pair, current_time, current_price, event))
                redis.rm_drawup(pair)
                redis.rm_drawdown(pair)

        trade.close_trade(sells, drawdowns=drawdowns, drawups=drawups)
        trade.open_trade(buys)

    print(get_recent_profit(True, interval))

@GET_EXCEPTIONS
def prod_int_check(interval, test):
    """Check price between candles for slippage below stoploss"""
    dbase = Mysql(test=False, interval=interval)
    current_trades = dbase.get_trades()
    redis = Redis(interval=interval, test=False)
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    sells = []
    drawdowns = {}
    drawups = {}
    for trade in current_trades:
        pair = trade[0]
        open_price = dbase.get_trade_value(pair)[0][0]
        dataframes = get_dataframes([pair], interval=interval, no_of_klines=1)
        current_candle = dataframes[pair].iloc[-1]
        redis.update_drawdown(pair, current_candle)
        redis.update_drawup(pair, current_candle)
        result, event, current_time, current_price = redis.get_intermittent(pair,
                                                                            open_price,
                                                                            current_candle)

        LOGGER.debug("%s int check result: %s Buy:%s Current:%s Time:%s"
                     % (pair, result, open_price, current_price, current_time))
        if result == "CLOSE":
            LOGGER.debug("Items to sell")
            sells.append((pair, current_time, current_price, event))
            drawdowns[pair] = redis.get_drawdown(pair)
            drawups[pair] = redis.get_drawup(pair)['perc']
            redis.rm_drawup(pair)
            redis.rm_drawdown(pair)

    trade = Trade(interval=interval, test_trade=test, test_data=False)
    trade.close_trade(sells, drawdowns=drawdowns, drawups=drawups)
    del redis
    del dbase

@GET_EXCEPTIONS
def prod_initial(interval, test=False):
    """
    Initial prod run - back-fetching data for tech analysis.
    """
    prices = binance.prices()
    prices_trunk = {}

    for key, val in prices.items():
        if key in PAIRS:
            prices_trunk[key] = val


    # Number of klines for a given number of seconds
    multiplier = {'1d': 3600 * 24,
                  '4h': 3600 * 4,
                  '2h': 3600 * 2,
                  '1h': 3600,
                  '30m': 3600 / 2,
                  '15m': 3600 / 4,
                  '5m': 3600 / 12,
                  '3m': 3600 / 20,
                  '1m': 3600 / 60
                 }


    redis = Redis(interval=interval, test=test)
    if interval == '4h':
        try:
            last_item = redis.get_items(PAIRS[0], interval)[-1]
            last_epoch = int(int(last_item.decode("utf-8").split(':')[-1])/1000)+1
            current_epoch = time.time()
            time_since_last = current_epoch - last_epoch
            no_of_klines = int(time_since_last / multiplier[interval] + 3)
        except IndexError:
            no_of_klines = config.main.no_of_klines
    else:
        no_of_klines = config.main.no_of_klines

    dataframes = get_dataframes(PAIRS, interval=interval, no_of_klines=no_of_klines)
    engine = Engine(prices=prices_trunk, dataframes=dataframes, interval=interval, test=test,
                    redis=redis)
    engine.get_data(localconfig=MAIN_INDICATORS, first_run=True, no_of_klines=no_of_klines)
    del redis

@GET_EXCEPTIONS
def prod_loop(interval, test_trade):
    """
    Loop through collection cycle (PROD)
    """

    LOGGER.debug("Performaing prod loop")
    LOGGER.info("Pairs in config: %s" % PAIRS)
    LOGGER.info("Total unique pairs: %s" % len(PAIRS))

    LOGGER.info("Starting new cycle")
    LOGGER.debug("max trades: %s" % config.main.max_trades)

    prices = binance.prices()
    prices_trunk = {}
    for key, val in prices.items():
        if key in PAIRS:
            prices_trunk[key] = val
    dataframes = get_dataframes(PAIRS, interval=interval)

    redis = Redis(interval=interval, test=False)
    engine = Engine(prices=prices_trunk, dataframes=dataframes, interval=interval, redis=redis)
    engine.get_data(localconfig=MAIN_INDICATORS, first_run=False)
    buys = []
    sells = []
    drawdowns = {}
    drawups = {}
    dataframes = get_dataframes(PAIRS, interval=interval, no_of_klines=1)
    for pair in PAIRS:
        result, event, current_time, current_price, _ = redis.get_action(pair=pair,
                                                                         interval=interval)
        current_candle = dataframes[pair].iloc[-1]
        redis.update_drawdown(pair, current_candle)
        redis.update_drawup(pair, current_candle)

        if result == "OPEN":
            LOGGER.debug("Items to buy")
            redis.update_drawdown(pair, current_candle, event='open')
            redis.update_drawup(pair, current_candle, event='open')
            buys.append((pair, current_time, current_price, event))
        if result == "CLOSE":
            LOGGER.debug("Items to sell")
            sells.append((pair, current_time, current_price, event))
            drawdowns[pair] = redis.get_drawdown(pair)
            drawups[pair] = redis.get_drawup(pair)['perc']
            redis.rm_drawup(pair)
            redis.rm_drawdown(pair)

    trade = Trade(interval=interval, test_trade=test_trade, test_data=False)
    trade.close_trade(sells, drawdowns=drawdowns, drawups=drawups)
    trade.open_trade(buys)
    del engine
    del redis
