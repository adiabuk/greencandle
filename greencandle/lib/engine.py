#pylint: disable=no-member,consider-iterating-dictionary,broad-except,
#pylint: disable=unused-variable,possibly-unused-variable,redefined-builtin,unused-import

"""
Module for collecting price data and creating TA results
"""

from __future__ import print_function
import json
import math
import sys
import traceback
import operator
from time import time
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import pickle
import zlib
import pandas
import talib
from indicator import SuperTrend, RSI

from . import config

from .redis_conn import Redis
from .supres import supres
from .common import make_float, pipify, pip_calc
from .logger import get_logger, get_decorator

LOGGER = get_logger(__name__)

class Engine(dict):
    """ Represent events created from data & indicators """

    get_exceptions = get_decorator((Exception))
    def __init__(self, dataframes, prices, interval=None, test=False, redis=None):
        """
        Initialize class
        Create hold and event dicts
        Fetch initial data from binance and store within object
        """
        LOGGER.debug("Fetching raw data")
        self.interval = interval
        self.pairs = prices.keys()
        self.test = test
        self.redis = redis
        self["hold"] = {}
        self["event"] = {}
        self.supres = {}
        self.current_time = str(int(time()*1000))
        self.dataframes = dataframes
        self.schemes = []
        super(Engine, self).__init__()
        LOGGER.debug("Finished fetching raw data")

    @staticmethod
    def make_data_tupple(dataframe):
        """
        Transform dataframe to tupple of of floats
        """
        ohlc = (make_float(dataframe.open),
                make_float(dataframe.high),
                make_float(dataframe.low),
                make_float(dataframe.close))

        return ohlc

    def get_json(self):
        """return serialized JSON of dict """
        return json.dumps(self)

    @staticmethod
    def renamed_dataframe_columns(klines=None):
        """
        Return dataframe with ordered/renamed coulumns
        Rename dataframe columns and reorder, only fetch columns that we care about
        Args:
              klines: pandas dataframe containing data for specified pair
        Returns:
              klines: pandas dataframe with modified column names and ordering
        """


        dataframe = pandas.DataFrame(klines, columns=["openTime", "open", "high",
                                                      "low", "close", "volume"])
        columns = ["date", "Open", "High", "Low", "Close", "Volume"]  # rename columns
        for index, item in enumerate(columns):
            dataframe.columns.values[index] = item
        return dataframe

    @staticmethod
    def get_url(pair):
        """
        Get tradingview graph URL for given pair

        Args:
            pair: trading pair (eg. XRPBTC)
        Returns:
            String URL for given pair

        """

        return "https://uk.tradingview.com/symbols/{0}/".format(pair)

    @staticmethod
    def get_supertrend_direction(supertrend):
        """
        Get new direction of supertrend from pattern

        Args:
            supertrend: list of trend directions (up/down)
        Returns:
            String action based on patten (BUY/SELL/HOLD/UNKNOWN)

        """
        if supertrend == "up":
            result = 1, "BUY"
        elif supertrend == "down":
            result = 2, "SELL"
        else:
            result = 0, "HOLD"
        return result

    @staticmethod
    def get_operator_fn(symbol):
        """
        Get operator function from string
        Args:
            symbol: string operator "<" or ">"
        Returns:
            operator.lt or operator.gt function
        """

        return {
            "<" : operator.lt,
            ">" : operator.gt,
            }[symbol]

    @get_exceptions
    def eval_binary_expr(self, op1, oper, op2):
        """
        Evaluate a binary expression
        eg 2 > 5, 0.12123 < 0.121
        Args:
            op1: value #1
            oper: string operator "<" or ">"
            op2: value #2
        Returns:
            Boolean result of binary expression (True/False)
        """

        op1, op2 = float(op1), float(op2)
        return self.get_operator_fn(oper)(op1, op2)

    @get_exceptions
    def add_schemes(self):
        """ add scheme to correct structure """

        for scheme in self.schemes:
            pair = scheme["symbol"]
            # add to redis
            current_price = str(Decimal(self.dataframes[pair].iloc[-1]["close"]))
            close_time = str(self.dataframes[pair].iloc[-1]["closeTime"]) if not "close_time" in \
                    scheme else scheme["close_time"]

            # close time might be in the future if we run between open/close
            if datetime.fromtimestamp(int(close_time)/1000) > datetime.now():
                close_time = self.current_time

            result = None if (isinstance(scheme["data"], float) and
                              math.isnan(scheme["data"]))  else scheme["data"]
            try:
                data = {scheme["event"]:{"result": result,
                                         "current_price": format(float(current_price), ".20f"),
                                         "date": close_time,
                                         }}

                self.redis.redis_conn(pair, self.interval, data, close_time)

            except Exception as exc:
                LOGGER.critical("Redis failure %s %s", str(exc), repr(sys.exc_info()))
        self.schemes = []

    @get_exceptions
    def get_data(self, localconfig=None, first_run=False):
        """
        Iterate through data and trading pairs to extract data
        Run data through indicator, oscillators, moving average
        Return dict containing alert data and hold data

        Args: None

        Returns:
            dict containing all collected data
        """
        LOGGER.debug("Getting data")
        for pair in self.pairs:

            # get indicators supertrend, and API for each trading pair
            with ThreadPoolExecutor(max_workers=100) as pool:

                for item in localconfig:
                    function, name, period = item.split(';')
                    # call each method defined in config with current pair and name,period tuple
                    # from config eg. self.supertrend(pair, config), where config is a tuple
                    # each method has the method name in 'function't st

                    pool.submit(getattr(self, function)(pair, self.dataframes[pair], index=None,
                                                        localconfig=(name, period)))
                    if first_run:
                        for seq in range(int(config.main.no_of_klines) -1):
                            pool.submit(getattr(self, function)(pair, self.dataframes[pair],
                                                                index=seq,
                                                                localconfig=(name, period)))

                pool.shutdown(wait=True)

            self.send_ohlcs(pair, first_run=first_run)
        self.add_schemes()

        LOGGER.debug("Done getting data")
        return self

    def send_ohlcs(self, pair, first_run):
        """Send ohcls data to redis"""
        scheme = {}
        scheme["symbol"] = pair
        # Unless we are in test mode, use the second to last data row as the previous one is still
        # being constructed and contains incomplete data
        location = -1 if self.test else -2

        # compress and pickle current dataframe for redis storage
        # dont get most recent one, as it may not be complete
        scheme['data'] = zlib.compress(pickle.dumps(self.dataframes[pair].iloc[location]))
        scheme["event"] = "ohlc"

        #self.add_scheme(scheme)
        self.schemes.append(scheme)
        if first_run:
            for seq in range(int(config.main.no_of_klines) -1):
                LOGGER.info("Getting initial sequence number %s", seq)
                scheme['data'] = zlib.compress(pickle.dumps(self.dataframes[pair].iloc[seq]))
                scheme["event"] = "ohlc"
                scheme["close_time"] = str(self.dataframes[pair].iloc[seq]["closeTime"])
                self.schemes.append(scheme)
                #self.add_scheme(scheme)

    @get_exceptions
    def get_sup_res(self, pair, dataframe, index=None, localconfig=None):
        """
        get support & resistance values for current pair
        Append data to supres instance variable (dict)

        Args:
              pair: trading pair (eg. XRPBTC)
              localconfig: indicator config tuple
        Returns:
            None
        """

        func, timeperiod = localconfig  # split tuple
        LOGGER.info("Getting Support & resistance for %s", pair)

        close_values = make_float(dataframe.close)[:index]
        support, resistance = supres(close_values, int(timeperiod))
        scheme = {}
        try:
            value = (pip_calc(support[-1], resistance[-1]))
        except IndexError:
            LOGGER.debug("Skipping %s %s %s for support/resistance",
                         pair, str(support), str(resistance))
            return None

        cur_to_res = resistance[-1] - close_values[-1]
        cur_to_sup = close_values[-1] - support[-1]
        data = {}

        try:
            scheme["difference"] = pipify(resistance[-1]) - pipify(support[-1])
        except TypeError as type_error:
            print("Type error", support[-1], resistance[-1], type_error)
            return None
        if func == 'RES':
            scheme["data"] = str(resistance[-1])
        elif func == 'SUP':
            scheme["data"] = str(support[-1])
        scheme["symbol"] = pair
        scheme["event"] = "{0}_{1}".format(func, timeperiod)
        scheme["close_time"] = str(self.dataframes[pair].iloc[index or -1]["closeTime"])
        #self.add_scheme(scheme)
        self.schemes.append(scheme)
        LOGGER.debug("Done getting Support & resistance")
        return None

    def get_bb(self, pair, dataframe, index=None, localconfig=None):
        """get bollinger bands"""

        LOGGER.debug("Getting bollinger bands for %s", pair)
        klines = self.make_data_tupple(dataframe.iloc[:index])
        func, timef = localconfig  # split tuple
        timeframe, multiplier = timef.split(',')
        results = {}
        try:
            close = klines[-1]
        except Exception as exc:
            LOGGER.critical("FAILED bbands: %s ", str(exc))
        try:
            upper, middle, lower = \
                    talib.BBANDS(close * 100000, timeperiod=int(timeframe),
                                 nbdevup=float(multiplier), nbdevdn=float(multiplier), matype=0)

            results['upper'] = upper[-1]/100000
            results['middle'] = middle[-1]/100000
            results['lower'] = lower[-1]/100000

        except Exception as exc:
            results['upper'] = 0
            results['middle'] = 0
            results['lower'] = 0
            LOGGER.critical("Overall Exception getting bollinger bands: %s", exc)
        trigger = None
        scheme = {}
        try:
            current_price = str(Decimal(self.dataframes[pair].iloc[-1]["close"]))

            scheme["data"] = results[func]
            scheme["symbol"] = pair
            scheme["event"] = "{0}_{1}".format(func, timeframe)
            scheme["close_time"] = str(self.dataframes[pair].iloc[index or -1]["closeTime"])

            self.schemes.append(scheme)
            #self.add_scheme(scheme)

        except KeyError as exc:
            LOGGER.critical("KEY FAILURE in bollinger bands: %s ", str(exc))

        LOGGER.debug("Done getting Bollinger bands")

    @get_exceptions
    def get_rsi(self, pair, dataframe, index=None, localconfig=None):
        """
        get RSI oscillator values for given pair
        Append current RSI data to instance variable

        Args:
              pair: trading pair (eg. XRPBTC)
              localconfig: indicator config tuple
        Returns:
            None

        """
        func, timeperiod = localconfig  # split tuple
        LOGGER.debug("Getting %s_%s for %s", func, timeperiod, pair)
        dataframe = self.renamed_dataframe_columns(dataframe)
        scheme = {}
        mine = dataframe.apply(pandas.to_numeric).loc[:index]

        rsi = RSI(mine, base='Close', period=int(timeperiod))
        df_list = rsi["{0}_{1}".format(func, timeperiod)].tolist()
        df_list = ["%.1f" % float(x) for x in df_list]
        scheme["data"] = df_list[-1]
        scheme["symbol"] = pair
        scheme["event"] = "{0}_{1}".format(func, timeperiod)
        scheme["close_time"] = str(self.dataframes[pair].iloc[index or -1]["closeTime"])

        self.schemes.append(scheme)
        #self.add_scheme(scheme)
        LOGGER.debug("Done getting RSI")

    @get_exceptions
    def get_hma(self, pair, dataframe, index=None, localconfig=None):
        """
        Calculate Hull Moving Average using Weighted Moving Average
        """
        klines = self.make_data_tupple(dataframe.iloc[:index])
        func, timeperiod = localconfig
        close = klines[-1]
        first = talib.WMA(close, int(timeperiod)/2)
        second = talib.WMA(close, int(timeperiod))

        result = talib.WMA((2 * first) - second, round(math.sqrt(int(timeperiod))))[-1]
        trigger = "BUY"
        if result > close[-1]:
            trigger = "SELL"
        else:
            trigger = "BUY"
        scheme = {}

        try:
            scheme["data"] = result
            scheme["symbol"] = pair
            scheme["event"] = func+"_"+str(timeperiod)
            scheme["close_time"] = str(self.dataframes[pair].iloc[index or -1]["closeTime"])

            self.schemes.append(scheme)
            #self.add_scheme(scheme)

        except KeyError as exc:
            LOGGER.critical("KEY FAILURE in moving averages: %s ", str(exc))

        LOGGER.debug("done getting moving averages")

    @get_exceptions
    def get_moving_averages(self, pair, dataframe, index=None, localconfig=None, volume=False):
        """
        Apply moving averages to klines and get BUY/SELL triggers
        Add data to DB

        Args:
            pair: trading pair (eg. XRPBTC)
            localconfig: indicator config tuple

        Returns:
            None
        """
        LOGGER.debug("Getting moving averages for %s", pair)
        klines = self.make_data_tupple(dataframe.iloc[:index])
        func, timeperiod = localconfig  # split tuple
        try:
            close = klines[-1] # numpy.ndarray
        except Exception as exc:
            LOGGER.critical("FAILED moving averages: %s ", str(exc))
        try:
            result = getattr(talib, func)(close, int(timeperiod))[-1]
        except Exception as exc:
            LOGGER.critical("Overall Exception getting moving averages: %s", exc)

        scheme = {}
        result = None if math.isnan(result) else format(float(result), ".20f")
        try:
            scheme["data"] = result
            scheme["symbol"] = pair
            scheme["event"] = func + "_" + str(timeperiod)
            scheme["close_time"] = str(self.dataframes[pair].iloc[index or -1]["closeTime"])

            self.schemes.append(scheme)
            #self.add_scheme(scheme)

        except KeyError as exc:
            LOGGER.critical("KEY FAILURE in moving averages: %s ", str(exc))

        LOGGER.debug("done getting moving averages")

    @get_exceptions
    def get_oscillators(self, pair, dataframe, index=None, localconfig=None):
        """

        Apply osscilators to klines and get BUY/SELL triggers
        Add data to DB

        Args:
            pair: trading pair (eg. XRPBTC)
            localconfig: indicator config tuple

        Returns:
            None
        """
        LOGGER.debug("Getting Oscillators for %s", pair)
        klines = self.make_data_tupple(dataframe.iloc[:index])
        open, high, low, close = klines
        func, timeperiod = localconfig  # split tuple

        scheme = {}
        trends = {
            "STOCHF": {"args":[20], "klines":("high", "low", "close")},
            #"CCI": {"klines": ("high", "low", "close"), "args": [14]},
            #"RSI": {"klines": tuple(("close",)), "args": [14]},
            #"MOM": {"klines": tuple(("close",)), "args": [10]},
            #"APO": {"klines": tuple(("close",)), "args": []},
            #"ULTOSC": {"klines": ("high", "low", "close"), "args":[7, 14, 28]},
            #"WILLR": {"klines": ("high", "low", "close"), "args": [14]},
            #"AROONOSC": {"klines": ("high", "low"), "args": []}
            }
        check = func
        attrs = trends[func]
        try:

            li = []
            for i in attrs["klines"]:
                li.append(locals()[i])

            fastk, fastd = getattr(talib, func)(high, low, close, int(timeperiod))

        except Exception as error:
            traceback.print_exc()
            LOGGER.critical("failed getting oscillators: %s", str(error))
            return

        result = fastk[-1]
        try:
            scheme["data"] = result
            scheme["symbol"] = pair
            scheme["event"] = '{}_{}'.format(func, timeperiod)
            scheme["close_time"] = str(self.dataframes[pair].iloc[index or -1]["closeTime"])

            self.schemes.append(scheme)
            #self.add_scheme(scheme)

        except KeyError as error:
            LOGGER.critical("Key failure while getting oscillators: %s", str(error))
        LOGGER.debug("Done getting Oscillators")

    @get_exceptions
    def get_indicators(self, pair, dataframe, index=None, localconfig=None):
        """

        Cross Reference data against trend indicators
        Apply osscilators to klines and get BUY/SELL triggers

        Args:
            pair: trading pair (eg. XRPBTC)
            config: indicator config tuple

        Returns:
            None
        """
        func, timeperiod = localconfig
        klines = self.make_data_tupple(dataframe.iloc[:index])
        LOGGER.debug("Getting Indicators for %s", pair)
        scheme = {}
        trends = {"HAMMER": {100: "BUY", 0:"HOLD"},
                  "INVERTEDHAMMER": {100: "SELL", 0:"HOLD"},
                  "ENGULFING": {-100:"SELL", 100:"BUY", 0:"HOLD"},
                  "MORNINGSTAR": {-100:"SELL", 100:"BUY", 0:"HOLD"},
                  "SHOOTINGSTAR": {-100:"SELL", 100:"BUY", 0:"HOLD"},
                  "SPINNINGTOP": {-100:"SELL", 100:"BUY", 0:"HOLD"},
                  "MARUBOZU": {-100:"SELL", 100:"BUY", 0:"HOLD"},
                  "DOJI": {100: "HOLD", 0:"HOLD"}}

        result = getattr(talib, "CDL" + func)(*klines).tolist()[-1]

        scheme["data"] = result   # convert from array to list
        scheme["symbol"] = pair
        scheme["event"] = "{0}_{1}".format(func, timeperiod)
        scheme["close_time"] = str(self.dataframes[pair].iloc[index or -1]["closeTime"])

        self.schemes.append(scheme)
        #self.add_scheme(scheme)

        LOGGER.debug("Done getting Indicators")

    @get_exceptions
    def get_supertrend(self, pair, dataframe, index=None, localconfig=None):
        """
        Get the super trend oscillator values for a given pair
        append current supertrend data to instance variable

        Args:
              pair: trading pair (eg. XRPBTC)
              localconfig: indicator config tuple
        Returns:
            None

        """

        func, timef = localconfig  # split tuple
        LOGGER.debug("Getting supertrend for %s", pair)
        scheme = {}
        dataframe = self.renamed_dataframe_columns(dataframe)

        mine = dataframe.apply(pandas.to_numeric).loc[:index]
        timeframe, multiplier = timef.split(',')
        supertrend = SuperTrend(mine, int(timeframe), int(multiplier))
        df_list = supertrend["STX_{0}_{1}".format(timeframe, multiplier)].tolist()

        scheme["data"] = self.get_supertrend_direction(df_list[-1])[0]
        scheme["symbol"] = pair
        scheme["event"] = "Supertrend_{0},{1}".format(timeframe, multiplier)
        scheme["close_time"] = str(self.dataframes[pair].iloc[index or -1]["closeTime"])

        self.schemes.append(scheme)
        #self.add_scheme(scheme)
        LOGGER.debug("done getting supertrend")
