#pylint: disable=no-member, logging-not-lazy, broad-except

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
import requests
from binance.binance import Binance
from str2bool import str2bool
from greencandle.lib.auth import binance_auth
from greencandle.lib.engine import Engine
from greencandle.lib.redis_conn import Redis
from greencandle.lib.mysql import Mysql
from greencandle.lib.profit import get_recent_profit
from greencandle.lib.order import Trade
from greencandle.lib.binance_common import get_dataframes
from greencandle.lib.logger import get_logger, exception_catcher
from greencandle.lib import config

LOGGER = get_logger(__name__)
CHUNK_SIZE = int(config.main.no_of_klines)
GET_EXCEPTIONS = exception_catcher((Exception))
PAIRS = config.main.pairs.split()
MAIN_INDICATORS = config.main.indicators.split()

@GET_EXCEPTIONS
def serial_test(pairs, intervals, data_dir, indicators):
    """
    Do test with serial data
    """
    LOGGER.debug("Performaing serial run")

    for pair in pairs:
        pair = pair.strip()
        for interval in intervals:
            dbase = Mysql(test=True, interval=interval)
            dbase.delete_data()
            del dbase
            redis = Redis(test_data=True)
            redis.clear_all()
            del redis

        for interval in intervals:
            with ThreadPoolExecutor(max_workers=len(intervals)) as pool:
                pool.submit(perform_data, pair, interval, data_dir, indicators)

@GET_EXCEPTIONS
def perform_data(pair, interval, data_dir, indicators):
    """Serial test loop"""
    pair = pair.strip()
    LOGGER.debug("Serial run %s %s" % (pair, interval))
    redis = Redis(interval=interval, test_data=True)
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
        trade = Trade(interval=interval, test_trade=True, test_data=True, config=config)

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
        action = 1 if config.main.trade_direction == 'long' else -1
        if result == "OPEN":
            buys.append((pair, current_time, current_price, event, action))
            LOGGER.debug("Items to buy: %s" % buys)
            trade_result = trade.open_trade(buys)
            if trade_result:
                redis.update_drawdown(pair, current_candle, event='open')
                redis.update_drawup(pair, current_candle, event='open')
            else:
                LOGGER.info("Unable to open trade")

        elif result == "CLOSE":
            sells.append((pair, current_time, current_price, event, 0))
            LOGGER.debug("Items to sell: %s" % sells)
            drawdown = redis.get_drawdown(pair)
            drawup = redis.get_drawup(pair)['perc']
            trade_result = trade.close_trade(sells, drawdowns={pair:drawdown},
                                             drawups={pair:drawup})
            if trade_result:
                redis.rm_drawup(pair)
                redis.rm_drawdown(pair)
            else:
                LOGGER.info("Unable to close trade")

    LOGGER.info("Selling remaining item")
    sells = []
    if current_trade:
        sells.append((pair, current_time, current_price, event, 0))
        current_candle = dataframes[pair].iloc[-1]

        redis.update_drawdown(pair, current_candle)
        redis.update_drawup(pair, current_candle)

        drawdown = redis.get_drawdown(pair)
        drawup = redis.get_drawup(pair)['perc']
        trade_result = trade.close_trade(sells, drawdowns={pair:drawdown}, drawups={pair:drawup})
        if trade_result:
            redis.rm_drawup(pair)
            redis.rm_drawdown(pair)


    del redis
    del dbase

def parallel_test(pairs, interval, data_dir, indicators):
    """
    Do test with parallel data
    """
    LOGGER.info("Performaing parallel run %s" % interval)
    redis = Redis(test_data=True)
    redis.clear_all()
    dbase = Mysql(test=True, interval=interval)
    dbase.delete_data()
    del dbase
    trade = Trade(interval=interval, test_trade=True, test_data=True, config=config)
    dframes = {}
    sizes = []
    for pair in pairs:
        pair = pair.strip()
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

            action = 1 if config.main.trade_direction == 'long' else -1
            if result == "OPEN":
                LOGGER.debug("Items to buy")
                redis.update_drawdown(pair, current_candle, event='open')
                redis.update_drawup(pair, current_candle, event='open')
                buys.append((pair, current_time, current_price, event, action))
            if result == "CLOSE":
                LOGGER.debug("Items to sell")
                drawdowns[pair] = redis.get_drawdown(pair)
                drawups[pair] = redis.get_drawup(pair)['perc']
                sells.append((pair, current_time, current_price, event, 0))
                redis.rm_drawup(pair)
                redis.rm_drawdown(pair)

        trade.close_trade(sells, drawdowns=drawdowns, drawups=drawups)
        trade.open_trade(buys)

    print(get_recent_profit(True, interval))

class ProdRunner():
    """
    Collect and OHLC and indicator data whilst preserving previous candles
    """
    def __init__(self):
        self.dataframes = {}

    @staticmethod
    @GET_EXCEPTIONS
    def prod_int_check(interval, test, alert=False):
        """Check price between candles for slippage below stoploss"""
        dbase = Mysql(test=False, interval=interval)
        redis = Redis()
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())

        for trade in dbase.get_trades():
            sells = []
            drawdowns = {}
            drawups = {}
            pair = trade[0].strip()
            open_price, _, open_time, _, _, _ = dbase.get_trade_value(pair)[0]

            klines = 10 if interval == '1m' else 3
            current_candle = get_dataframes([pair],
                                            interval=interval,
                                            no_of_klines=klines)[pair].iloc[-1]

            redis.update_drawdown(pair, current_candle, open_time=open_time)
            redis.update_drawup(pair, current_candle, open_time=open_time)
            result, event, current_time, current_price = redis.get_intermittent(pair,
                                                                                open_price,
                                                                                current_candle,
                                                                                open_time)

            LOGGER.debug("%s int check result: %s Buy:%s Current:%s Time:%s"
                         % (pair, result, open_price, current_price, current_time))
            if result == "CLOSE":
                LOGGER.debug("Items to sell")
                sells.append((pair, current_time, current_price, event, 0))
                drawdowns[pair] = redis.get_drawdown(pair)
                drawups[pair] = redis.get_drawup(pair)['perc']
                if alert:
                    payload = {"pair":pair, "strategy":"alert",
                               "text": "Closing API trade according to TP/SL rules",
                               "action":"close"}
                    host = os.environ['HOST_IP']
                    url = "http://{}:1080/{}".format(host, config.web.api_token)
                    try:
                        requests.post(url, json=payload, timeout=1)
                    except Exception:
                        pass

                trade = Trade(interval=interval, test_trade=test, test_data=False, config=config)
                trade.close_trade(sells, drawdowns=drawdowns, drawups=drawups)

                redis.rm_drawup(pair)
                redis.rm_drawdown(pair)
                redis.rm_on_entry(pair, "take_profit_perc")
                redis.rm_on_entry(pair, "stop_loss_perc")
        del redis
        del dbase

    @GET_EXCEPTIONS
    def prod_initial(self, interval, test=False):
        """
        Initial prod run - back-fetching data for tech analysis.
        """
        client = Binance(debug=str2bool(config.accounts.account_debug))
        prices = client.prices()
        prices_trunk = {}

        for key, val in prices.items():
            if key in PAIRS:
                prices_trunk[key] = val

        redis = Redis()
        no_of_klines = config.main.no_of_klines
        LOGGER.debug("Getting %s klines" % no_of_klines)
        self.dataframes = get_dataframes(PAIRS, interval=interval, no_of_klines=no_of_klines)
        for pair, dframe in self.dataframes.items():
            self.dataframes[pair] = dframe[:-1]
        engine = Engine(prices=prices_trunk, dataframes=self.dataframes, interval=interval,
                        test=test, redis=redis)
        engine.get_data(localconfig=MAIN_INDICATORS, first_run=True, no_of_klines=no_of_klines)
        del redis

    def append_data(self, interval):
        """
        Fetch new dataframe data and append to existing structure
        """

        new_dataframes = get_dataframes(PAIRS, interval=interval, no_of_klines=2)
        max_klines = int(config.main.no_of_klines)
        for pair in PAIRS:
            # skip pair if empty dataframe (no new trades in kline)
            if len(new_dataframes[pair]) == 0:
                continue
            # get last column of new data
            for _, row in new_dataframes[pair].iterrows():
                # use closeTime as index
                new_close = row['closeTime']
                # see if closeTime already exists in data
                old_index = self.dataframes[pair].index[self.dataframes[pair]['closeTime'] ==
                                                        new_close].tolist()
                if old_index:
                    # if it exsits, then we use the last index occurance in list
                    # and overwrite that field in existing data
                    self.dataframes[pair].loc[old_index[-1]] = row
                else:
                    # otherwise just append the data to the end of the dataframe
                    self.dataframes[pair] = \
                            self.dataframes[pair].append(new_dataframes[pair],
                                                         ignore_index=True).tail(max_klines)

    @GET_EXCEPTIONS
    def prod_loop(self, interval, test=False, data=True, analyse=True):
        """
        Loop through collection cycle (PROD)
        """
        LOGGER.debug("Performaing prod loop")
        LOGGER.info("Pairs in config: %s" % PAIRS)
        LOGGER.info("Total unique pairs: %s" % len(PAIRS))

        LOGGER.info("Starting new cycle")
        LOGGER.debug("max trades: %s" % config.main.max_trades)
        client = Binance(debug=str2bool(config.accounts.account_debug))
        redis = Redis()

        if data:
            prices = client.prices()
            prices_trunk = {}
            for key, val in prices.items():
                if key in PAIRS:
                    prices_trunk[key] = val
            self.append_data(interval)
            engine = Engine(prices=prices_trunk, dataframes=self.dataframes, interval=interval,
                            redis=redis)
            engine.get_data(localconfig=MAIN_INDICATORS, first_run=False)
            del engine
        if analyse:
            buys = []
            sells = []
            drawdowns = {}
            drawups = {}

            for pair in PAIRS:
                pair = pair.strip()
                result, event, current_time, current_price, _ = redis.get_action(pair=pair,
                                                                                 interval=interval)
                current_candle = redis.get_last_candle(pair, interval)
                client = binance_auth()
                if result != "NOITEM":
                    redis.update_drawdown(pair, current_candle)
                    redis.update_drawup(pair, current_candle)

                action = 1 if config.main.trade_direction == 'long' else -1
                if result == "OPEN":
                    LOGGER.debug("Items to buy")
                    tick = client.tickers()
                    current_price = tick[pair]['ask'] if config.main.trade_direction == 'long' \
                            else tick[pair]['bid']
                    redis.update_drawdown(pair, current_candle, event='open')
                    redis.update_drawup(pair, current_candle, event='open')
                    buys.append((pair, current_time, current_price, event, action))

                if result == "CLOSE":
                    LOGGER.debug("Items to sell")
                    tick = client.tickers()
                    current_price = tick[pair]['bid'] if config.main.trade_direction == 'long' \
                            else tick[pair]['ask']
                    sells.append((pair, current_time, current_price, event, 0))
                    drawdowns[pair] = redis.get_drawdown(pair)
                    drawups[pair] = redis.get_drawup(pair)['perc']
                    redis.rm_drawup(pair)
                    redis.rm_drawdown(pair)

            trade = Trade(interval=interval, test_trade=test, test_data=False, config=config)
            trade.close_trade(sells, drawdowns=drawdowns, drawups=drawups)
            trade.open_trade(buys)
            del redis
