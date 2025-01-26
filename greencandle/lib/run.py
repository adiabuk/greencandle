#pylint: disable=no-member,broad-except,too-many-locals,too-many-statements,consider-using-with, logging-fstring-interpolation

"""
Perform run for test & prod
"""
import gc
import os
import time
import pickle
import gzip
from glob import glob
from concurrent.futures import ThreadPoolExecutor
from collections import defaultdict
import pandas
import requests
from greencandle.lib.binance import Binance
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

        with ThreadPoolExecutor(max_workers=len(intervals)) as pool:
            for interval in intervals:
                pool.submit(perform_data, pair, interval, data_dir, indicators)
        pool.shutdown(wait=True)

@GET_EXCEPTIONS
def perform_data(pair, interval, data_dir, indicators):
    """Serial test loop"""
    pair = pair.strip()
    LOGGER.debug("Serial run %s %s", pair, interval)
    redis = Redis(interval=interval, test_data=True)

    dframe = get_pickle_data(pair, data_dir, interval)
    if not isinstance(dframe, pandas.DataFrame):
        return
    dbase = Mysql(test=True, interval=interval)
    current_trade = False
    print(len(dframe), CHUNK_SIZE)
    for beg in range(len(dframe) - CHUNK_SIZE):
        LOGGER.debug("in loop %s", beg)
        trade = Trade(interval=interval, test_trade=True, test_data=True, config=config)

        closes = []
        opens = []
        end = beg + CHUNK_SIZE
        LOGGER.debug("chunk: %s, %s", beg, end)
        dataframe = dframe.copy()[beg: end]

        current_otime = int(dataframe.iloc[-1].openTime)/1000
        current_time = time.strftime("%Y-%m-%d %H:%M:%S",
                                     time.gmtime(current_otime))
        LOGGER.debug("current date: %s", current_time)

        if len(dataframe) < CHUNK_SIZE:
            LOGGER.debug("End of dataframe")
            break
        dataframes = {pair:dataframe}
        engine = Engine(dataframes=dataframes,
                        interval=interval, test=True, redis=redis)
        engine.get_data(localconfig=indicators)

        result, event, current_time, current_price, _ = redis.get_rule_action(pair=pair,
                                                                              interval=interval)
        del engine
        current_trade = dbase.get_trade_value(pair)
        current_candle = dataframes[pair].iloc[-1]
        redis.update_drawdown(pair, current_candle)
        redis.update_drawup(pair, current_candle)
        action = 1 if config.main.trade_direction == 'long' else -1
        if result == "OPEN" and current_trade[0][0] is None:
            opens.append((pair, current_time, current_price, event, action, None))
            LOGGER.debug("Items to open: %s", opens)
            trade_result = trade.open_trade(opens)
            if trade_result:
                redis.update_drawdown(pair, current_candle, event='open')
                redis.update_drawup(pair, current_candle, event='open')
            else:
                LOGGER.info("Unable to open trade")

        elif result == "CLOSE" and current_trade[0][0] is not None:
            closes.append((pair, current_time, current_price, event, 0, 100))
            LOGGER.debug("Items to close: %s", closes)
            drawdown = redis.get_drawdown(pair)['perc']
            drawup = redis.get_drawup(pair)['perc']
            trade_result = trade.close_trade(closes, drawdowns={pair:drawdown},
                                             drawups={pair:drawup})
            if not trade_result:
                LOGGER.info("Unable to close trade")

    LOGGER.info("Closing remaining item")
    closes = []
    if current_trade:
        closes.append((pair, current_time, current_price, event, 0, 100))
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
    LOGGER.info("Performaing parallel run %s", interval)
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
        LOGGER.info("%s dataframe size: %s", pair, len(dframes[pair]))

    for beg in range(max(sizes) - CHUNK_SIZE):
        end = beg + CHUNK_SIZE
        dataframes = {}
        opens = []
        closes = []
        drawdowns = {}
        drawups = {}
        for pair in pairs:
            LOGGER.info("Current loop: %s to %s pair:%s", beg, end, pair)
            dataframe = dframes[pair][beg: end]
            if len(dataframe) < CHUNK_SIZE:
                break
            dataframes.update({pair:dataframe})
            engine = Engine(dataframes=dataframes,
                            interval=interval, test=True, redis=redis)
            engine.get_data(localconfig=indicators)

            result, event, current_time, current_price, _ = redis.get_rule_action(pair=pair,
                                                                                  interval=interval)
            current_candle = dataframe.iloc[-1]
            redis.update_drawdown(pair, current_candle)
            redis.update_drawup(pair, current_candle)

            LOGGER.info('In Strategy %s', result)
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
                closes.append((pair, current_time, current_price, event, 0, None))

        trade.close_trade(closes, drawdowns=drawdowns, drawups=drawups)
        trade.open_trade(opens)

    print(get_recent_profit(True, interval))

def get_pickle_data(pair, data_dir, interval):
    """
    Get dataframes from stored pickle file
    """
    try:
        filename = glob(f"{data_dir}/{pair}_{interval}.p*")[0]
        print(f"{data_dir}/{pair}_{interval}.p*")
    except IndexError:
        LOGGER.critical("Filename not found for %s %s", pair, interval)
        return None
    if not os.path.exists(filename):
        LOGGER.critical("Filename:%s not found for %s %s", filename, pair, interval)
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

        for trade in dbase.get_trades(config.main.trade_direction):
            closes = []
            drawdowns = {}
            drawups = {}
            pair, open_time, open_price = trade
            klines = 60 if interval.endswith('s') or interval.endswith('m') else 5

            stream = f'http://stream/{config.main.interval}/all'
            try:
                stream_req = requests.get(stream, timeout=10)
                prices = stream_req.json()
            except (requests.exceptions.ConnectTimeout, ValueError):
                prices = {}

            try:
                if 'recent' in prices and pair in prices['recent']:
                    current_candle = pandas.Series(prices['recent'][pair])
                else:
                    current_candle = get_dataframes([pair],
                                                    interval=interval,
                                                    no_of_klines=klines)[pair].iloc[-1]

            except IndexError:
                LOGGER.critical("unable to get %s candles for %s while running %s prod_int_check",
                                str(klines), pair, interval)
                # Ensure we skip iteration so we don't update db/redis
                # using values from previous loop
                continue

            redis.update_drawdown(pair, current_candle)
            redis.update_drawup(pair, current_candle)
            result, event, current_time, current_price = redis.get_intermittent(pair,
                                                                                open_price,
                                                                                current_candle,
                                                                                open_time)

            LOGGER.debug("%s int check result: %s Open:%s Current:%s Time:%s",
                         pair, result, open_price, current_price, current_time)
            if result == "CLOSE":
                LOGGER.debug("Items to close")
                closes.append((pair, current_time, current_price, event, 0, None))
                drawdowns[pair] = redis.get_drawdown(pair)['perc']
                drawups[pair] = redis.get_drawup(pair)['perc']
                if alert:
                    payload = {"pair":pair, "strategy":"alert", "host": "alert",
                               "text": "Closing API trade according to TP/SL rules",
                               "action":"close"}
                    url = f"http://router:1080/{config.web.api_token}"
                    try:
                        requests.post(url, json=payload, timeout=1)
                    except Exception:
                        pass

                trade = Trade(interval=interval, test_trade=test,
                              test_data=False, config=config)
                trade.close_trade(closes, drawdowns=drawdowns, drawups=drawups)

        del redis
        del dbase

    @GET_EXCEPTIONS
    def prod_initial(self, interval, test=False, first_run=True, no_of_runs=999):
        """
        Initial prod run - back-fetching data for tech analysis.
        """

        redis = Redis()
        no_of_klines = config.main.no_of_klines
        LOGGER.debug("Getting %s klines", no_of_klines)
        self.dataframes = get_dataframes(PAIRS, interval=interval, no_of_klines=no_of_klines)
        engine = Engine(dataframes=self.dataframes, interval=interval,
                        test=test, redis=redis)
        engine.get_data(localconfig=MAIN_INDICATORS, first_run=first_run, no_of_runs=no_of_runs)

        del redis
        del engine

    def append_data(self, interval=None):
        """
        Fetch new dataframe data and append to existing structure
        """

        request = requests.get(f"http://stream/{config.main.interval}/all", timeout=10)
        if not request.ok:
            LOGGER.critical("Unable to fetch data from streaming server")
            data = {'recent':{}, 'closed': {}}
        else:
            data = request.json()
        if len(data['recent'].keys()) < len(PAIRS):
            LOGGER.info("Insufficient data in stream, reverting to conventional method")
            klines = 60 if interval.endswith('s') or interval.endswith('m') else 5
            dataframes = get_dataframes(PAIRS, interval=interval, no_of_klines=klines)
            for pair in PAIRS:
                data['recent'][pair] = dict(dataframes[pair].iloc[-1])

        new_dataframes = defaultdict(dict)
        for pair in PAIRS:
            try:
                try:
                    recent_di = data['recent'][pair]
                except KeyError:
                    recent_di = None

                try:
                    closed_di = data['closed'][pair]
                except KeyError:
                    closed_di = None

                if not (recent_di or closed_di):
                    LOGGER.error(f"No candle data for pair {pair} - remove from config")
                    continue

                dframe = pandas.DataFrame(columns=recent_di.keys())
                if 'm' in interval and closed_di:
                    dframe.loc[0] = closed_di
                else:
                    dframe.loc[0] = recent_di

                new_dataframes[pair] = dframe.sort_values('openTime')
                del dframe
                del closed_di
            except ValueError:
                continue

        max_klines = int(config.main.no_of_klines)
        for pair in PAIRS:
            # skip pair if empty dataframe (no new trades in kline)
            if len(new_dataframes[pair]) == 0:
                continue

            if pair not in self.dataframes or len(self.dataframes[pair]) == 0:

                df2 = self.dataframes[pair].append(pandas.Series(data['recent'][pair]),
                                                   ignore_index=True,
                                                   verify_integrity=True).tail(max_klines)
                self.dataframes[pair] = df2
                continue


            if pair in data['closed'] and self.dataframes[pair].iloc[-1]['openTime'] == \
                    data['closed'][pair]['openTime'] and \
              self.dataframes[pair].iloc[-1]['numTrades'] < data['closed'][pair]['numTrades']:
                # candle closed
                self.dataframes[pair].iloc[-1] = pandas.Series(data['closed'][pair])

            elif self.dataframes[pair].iloc[-1]['openTime'] <  data['recent'][pair]['openTime']:
                # new candle
                df2 = self.dataframes[pair].append(pandas.Series(data['recent'][pair]),
                                                   ignore_index=True,
                                                   verify_integrity=True).tail(max_klines)
                self.dataframes[pair] = df2

            elif self.dataframes[pair].iloc[-1]['openTime'] == \
                    data['recent'][pair]['openTime'] and \
              self.dataframes[pair].iloc[-1]['numTrades'] < data['recent'][pair]['numTrades']:
                # updated candle
                self.dataframes[pair].iloc[-1] = pandas.Series(data['recent'][pair])

        gc.collect()

    @GET_EXCEPTIONS
    def prod_loop(self, interval, test=False, data=True, analyse=True):
        """
        Loop through collection cycle (PROD)
        """
        LOGGER.debug("starting new prod loop with %s pairs", len(PAIRS))
        client = Binance()
        redis = Redis()
        data = defaultdict(dict)

        if data:
            self.append_data(interval)
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
                result, event, current_time, current_price, match = \
                        redis.get_rule_action(pair=pair, interval=interval)
                for item in ('res', 'agg', 'sent'):
                    data[pair][item] = match[item]

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
            del trade
        del client
        del redis
        return data if analyse else True
