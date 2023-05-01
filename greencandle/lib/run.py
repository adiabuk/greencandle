#pylint: disable=no-member, logging-not-lazy, broad-except

"""
Perform run for test & prod
"""

import os
import time
import pickle
import gzip
from glob import glob
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
import pandas
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

    dframe = get_pickle_data(pair, data_dir, interval)
    if not isinstance(dframe, pandas.DataFrame):
        return
    dbase = Mysql(test=True, interval=interval)
    for beg in range(len(dframe) - CHUNK_SIZE):
        LOGGER.debug("IN LOOP %s " % beg)
        trade = Trade(interval=interval, test_trade=True, test_data=True, config=config)

        closes = []
        opens = []
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
        engine = Engine(dataframes=dataframes,
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
            opens.append((pair, current_time, current_price, event, action))
            LOGGER.debug("Items to open: %s" % opens)
            trade_result = trade.open_trade(opens)
            if trade_result:
                redis.update_drawdown(pair, current_candle, event='open')
                redis.update_drawup(pair, current_candle, event='open')
            else:
                LOGGER.info("Unable to open trade")

        elif result == "CLOSE":
            closes.append((pair, current_time, current_price, event, 0))
            LOGGER.debug("Items to close: %s" % closes)
            drawdown = redis.get_drawdown(pair)['perc']
            drawup = redis.get_drawup(pair)['perc']
            trade_result = trade.close_trade(closes, drawdowns={pair:drawdown},
                                             drawups={pair:drawup})
            if not trade_result:
                LOGGER.info("Unable to close trade")

    LOGGER.info("Closing remaining item")
    closes = []
    if current_trade:
        closes.append((pair, current_time, current_price, event, 0))
        current_candle = dataframes[pair].iloc[-1]

        redis.update_drawdown(pair, current_candle)
        redis.update_drawup(pair, current_candle)

        drawdown = redis.get_drawdown(pair)['perc']
        drawup = redis.get_drawup(pair)['perc']
        trade_result = trade.close_trade(closes, drawdowns={pair:drawdown}, drawups={pair:drawup})

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
        pickle_data = get_pickle_data(pair, data_dir, interval)
        if isinstance(pickle_data, pandas.DataFrame):
            dframes[pair] = pickle_data
        else:
            # skip to next pair if no data returned
            continue
        sizes.append(len(dframes[pair]))
        LOGGER.info("%s dataframe size: %s" % (pair, len(dframes[pair])))

    for beg in range(max(sizes) - CHUNK_SIZE):
        end = beg + CHUNK_SIZE
        dataframes = {}
        opens = []
        closes = []
        drawdowns = {}
        drawups = {}
        for pair in pairs:
            LOGGER.info("Current loop: %s to %s pair:%s" % (beg, end, pair))
            dataframe = dframes[pair][beg: end]
            if len(dataframe) < CHUNK_SIZE:
                break
            dataframes.update({pair:dataframe})
            engine = Engine(dataframes=dataframes,
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
                LOGGER.debug("Items to open")
                redis.update_drawdown(pair, current_candle, event='open')
                redis.update_drawup(pair, current_candle, event='open')
                opens.append((pair, current_time, current_price, event, action))
            if result == "CLOSE":
                LOGGER.debug("Items to close")
                drawdowns[pair] = redis.get_drawdown(pair)['perc']
                drawups[pair] = redis.get_drawup(pair)['perc']
                closes.append((pair, current_time, current_price, event, 0))

        trade.close_trade(closes, drawdowns=drawdowns, drawups=drawups)
        trade.open_trade(opens)

    print(get_recent_profit(True, interval))

def get_pickle_data(pair, data_dir, interval):
    """
    Get dataframes from stored pickle file
    """
    try:
        filename = glob("{0}/{1}_{2}.p*".format(data_dir, pair, interval))[0]
    except IndexError:
        LOGGER.critical("Filename not found for %s %s" % (pair, interval))
        return None
    if not os.path.exists(filename):
        LOGGER.critical("Filename:%s not found for %s %s" % (filename, pair, interval))
        return None
    if filename.endswith("gz"):
        handle = gzip.open(filename, "rb")
    else:
        handle = open(filename, "rb")
    dframe = pickle.load(handle)
    handle.close()
    return dframe

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
            closes = []
            drawdowns = {}
            drawups = {}
            pair = trade[0].strip()
            open_price, _, open_time, _, _, _ = dbase.get_trade_value(pair)[0]

            klines = 60 if interval.endswith('s') or interval.endswith('m') else 5
            try:
                current_candle = get_dataframes([pair],
                                                interval=interval,
                                                no_of_klines=klines)[pair].iloc[-1]
            except IndexError:
                LOGGER.critical("Unable to get %s candles for %s while performing %s prod_int_check"
                                % (str(klines), pair, interval))

            redis.update_drawdown(pair, current_candle, open_time=open_time)
            redis.update_drawup(pair, current_candle, open_time=open_time)
            result, event, current_time, current_price = redis.get_intermittent(pair,
                                                                                open_price,
                                                                                current_candle,
                                                                                open_time)

            LOGGER.debug("%s int check result: %s Open:%s Current:%s Time:%s"
                         % (pair, result, open_price, current_price, current_time))
            if result == "CLOSE":
                LOGGER.debug("Items to close")
                closes.append((pair, current_time, current_price, event, 0))
                drawdowns[pair] = redis.get_drawdown(pair)['perc']
                drawups[pair] = redis.get_drawup(pair)['perc']
                if alert:
                    payload = {"pair":pair, "strategy":"alert", "host": "alert",
                               "text": "Closing API trade according to TP/SL rules",
                               "action":"close"}
                    url = "http://router:1080/{}".format(config.web.api_token)
                    try:
                        requests.post(url, json=payload, timeout=1)
                    except Exception:
                        pass

                trade = Trade(interval=interval, test_trade=test, test_data=False, config=config)
                trade.close_trade(closes, drawdowns=drawdowns, drawups=drawups)

        del redis
        del dbase

    @GET_EXCEPTIONS
    def prod_initial(self, interval, test=False):
        """
        Initial prod run - back-fetching data for tech analysis.
        """

        redis = Redis()
        no_of_klines = config.main.no_of_klines
        LOGGER.debug("Getting %s klines" % no_of_klines)
        self.dataframes = get_dataframes(PAIRS, interval=interval, no_of_klines=no_of_klines)
        for pair, dframe in self.dataframes.items():
            self.dataframes[pair] = dframe[:-1]
        engine = Engine(dataframes=self.dataframes, interval=interval,
                        test=test, redis=redis)
        engine.get_data(localconfig=MAIN_INDICATORS, first_run=True, no_of_klines=no_of_klines)



        del redis

    def append_data(self):
        """
        Fetch new dataframe data and append to existing structure
        """

        new_dataframes = defaultdict(dict)
        for pair in PAIRS:
            try:
                request1 = requests.get("http://stream:5000/recent?pair={}".format(pair))
                request2 = requests.get("http://stream:5000/closed?pair={}".format(pair))
                recent_di = request1.json()

                try:
                    closed_di = request2.json()
                except ValueError:
                    closed_di = None

                dframe = pandas.DataFrame(columns=recent_di.keys())
                dframe.loc[0] = recent_di
                if closed_di and closed_di != recent_di:
                    dframe.loc[1] = closed_di
                new_dataframes[pair] = dframe.sort_values('closeTime')

            except ValueError:
                continue


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
                                                        str(new_close)].tolist()
                if old_index:
                    # if it exsits, then we use the last index occurance in list
                    # and overwrite that field in existing data
                    self.dataframes[pair].loc[old_index[-1]] = row
                else:
                    # otherwise just append the data to the end of the dataframe
                    self.dataframes[pair] = \
                        self.dataframes[pair].append(row, ignore_index=True,
                                                     verify_integrity=True).tail(max_klines)

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
            self.append_data()
            engine = Engine(dataframes=self.dataframes, interval=interval,
                            redis=redis)
            engine.get_data(localconfig=MAIN_INDICATORS, first_run=False)
            del engine
        if analyse:
            opens = []
            closes = []
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
                    LOGGER.debug("Items to open")
                    tick = client.tickers()
                    current_price = tick[pair]['ask'] if config.main.trade_direction == 'long' \
                            else tick[pair]['bid']
                    redis.update_drawdown(pair, current_candle, event='open')
                    redis.update_drawup(pair, current_candle, event='open')
                    opens.append((pair, current_time, current_price, event, action))

                if result == "CLOSE":
                    LOGGER.debug("Items to close")
                    tick = client.tickers()
                    current_price = tick[pair]['bid'] if config.main.trade_direction == 'long' \
                            else tick[pair]['ask']
                    closes.append((pair, current_time, current_price, event, 0))
                    drawdowns[pair] = redis.get_drawdown(pair)['perc']
                    drawups[pair] = redis.get_drawup(pair)['perc']

            trade = Trade(interval=interval, test_trade=test, test_data=False, config=config)
            trade.close_trade(closes, drawdowns=drawdowns, drawups=drawups)
            trade.open_trade(opens)
            del redis
