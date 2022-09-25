#pylint: disable=no-member,consider-iterating-dictionary,broad-except,logging-not-lazy,unused-import
#pylint: disable=unused-variable,possibly-unused-variable,redefined-builtin,global-statement,singleton-comparison

"""
Module for collecting price data and creating TA results
"""

from __future__ import print_function
import json
import math
import sys
import traceback
import operator
from time import time, strftime, localtime
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import pickle
import zlib
import pandas
import numpy
import pandas_ta as ta
import talib
from indicator import SuperTrend, RSI

from greencandle.lib import config
from greencandle.lib.common import make_float, pipify, pip_calc, epoch2date
from greencandle.lib.binance_common import get_all_klines
from greencandle.lib.logger import get_logger, exception_catcher

LOGGER = get_logger(__name__)
CROSS_DATA = {}  # data from different time period

class Engine(dict):
    """ Represent events created from data & indicators """

    get_exceptions = exception_catcher((Exception))
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
        self.current_time = str(int(time()*1000))
        self.dataframes = {}
        for key, value in dataframes.items():
            # Cleanout false datapoints
            value['closeTime'] = value['closeTime'].astype(str)
            self.dataframes[key] = value[value.closeTime.str.endswith('999')]
        self.schemes = []
        super().__init__()
        LOGGER.debug("Finished fetching raw data")

    @staticmethod
    def __make_data_tupple(dataframe):
        """
        Transform dataframe to tupple of of floats
        """
        ohlc = (make_float(dataframe.volume),
                make_float(dataframe.open),
                make_float(dataframe.high),
                make_float(dataframe.low),
                make_float(dataframe.close))

        return ohlc

    @staticmethod
    def __renamed_dataframe_columns(klines=None):
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
    def __add_schemes(self):
        """ add scheme to correct structure """

        for scheme in self.schemes:
            pair = scheme["symbol"]
            # add to redis
            current_price = str(Decimal(self.dataframes[pair].iloc[-1]["close"]))
            close_time = str(self.dataframes[pair].iloc[-1]["closeTime"]) if not "close_time" in \
                    scheme else scheme["close_time"]


            # close time might be in the future if we run between open/close

            if epoch2date(int(close_time)/1000, formatted=False) > datetime.now() and not self.test:
                continue

            result = None if (isinstance(scheme["data"], float) and
                              math.isnan(scheme["data"]))  else scheme["data"]
            try:
                data = {scheme["event"]:{"result": result,
                                         "current_price": format(float(current_price), ".20f"),
                                         "date": close_time,
                                         }}
                self.redis.redis_conn(pair, self.interval, data, close_time)

            except Exception as exc:
                LOGGER.critical("Redis failure %s %s" % (str(exc), repr(sys.exc_info())))
        self.schemes = []

    @get_exceptions
    def get_data(self, localconfig=None, first_run=False, no_of_klines=None):
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
            actual_klines = len(self.dataframes[pair]) if not no_of_klines else no_of_klines

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
                        for seq in range(int(actual_klines) -1):
                            pool.submit(getattr(self, function)(pair, self.dataframes[pair],
                                                                index=seq,
                                                                localconfig=(name, period)))

                pool.shutdown(wait=True)

            self.__send_ohlcs(pair, first_run=first_run, no_of_klines=no_of_klines)
        self.__add_schemes()

        LOGGER.debug("Done getting data")
        return self

    def __send_ohlcs(self, pair, first_run, no_of_klines=None):
        """Send ohcls data to redis"""
        scheme = {}
        scheme["symbol"] = pair
        # Unless we are in test mode, use the second to last data row as the previous one is still
        # being constructed and contains incomplete data
        location = -1 if (self.test or len(self.dataframes[pair]) < 2) else -2
        # compress and pickle current dataframe for redis storage
        # dont get most recent one, as it may not be complete
        try:
            close = float(self.dataframes[pair].iloc[location]["close"])
            if close <= 0:
                LOGGER.critical("Zero size dataframe found")
        except Exception as ex:
            LOGGER.critical("Non-float dataframe found")

        scheme['data'] = zlib.compress(pickle.dumps(self.dataframes[pair].iloc[location]))
        scheme["event"] = "ohlc"
        scheme["close_time"] = str(self.dataframes[pair].iloc[location]["closeTime"])

        self.schemes.append(scheme)
        actual_klines = len(self.dataframes[pair]) if not no_of_klines else no_of_klines
        if first_run:
            for seq in range(int(actual_klines) -1):
                LOGGER.debug("Getting initial sequence number %s" % seq)
                scheme['data'] = zlib.compress(pickle.dumps(self.dataframes[pair].iloc[seq]))
                scheme["event"] = "ohlc"
                scheme["close_time"] = str(self.dataframes[pair].iloc[seq]["closeTime"])
                self.schemes.append(scheme)

                # reset for next loop
                scheme = {"symbol": pair, "event": "ohlc"}

    def get_bb(self, pair, dataframe, index=None, localconfig=None):
        """get bollinger bands"""
        if (index == None and self.test) or len(self.dataframes[pair]) < 2:
            index = -1
        elif index == None and not self.test:
            index = -2
        close_time = str(self.dataframes[pair].iloc[index]["closeTime"])
        LOGGER.debug('AMROX787 %s %s' % (index, close_time))
        LOGGER.debug("Getting bollinger bands for %s - %s" % (pair, close_time))
        klines = self.__make_data_tupple(dataframe.iloc[:index])
        func, timef = localconfig  # split tuple
        timeframe, multiplier = timef.split(',')
        results = {}
        try:
            close = klines[-1]
        except Exception as exc:
            LOGGER.warning("FAILED bbands: %s " % str(exc))
            return
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
            LOGGER.warning("Overall Exception getting bollinger bands: %s" % exc)
        trigger = None
        scheme = {}
        try:
            current_price = str(Decimal(self.dataframes[pair].iloc[-1]["close"]))

            scheme["data"] = results[func]
            scheme["symbol"] = pair
            scheme["event"] = "{0}_{1}".format(func, timeframe)
            scheme["close_time"] = close_time

            self.schemes.append(scheme)

        except KeyError as exc:
            LOGGER.warning("KEY FAILURE in bollinger bands: %s" % str(exc))

        LOGGER.debug("Done getting Bollinger bands")

    @get_exceptions
    def get_pivot(self, pair, dataframe, index=None, localconfig=None):
        """
        Get pivot points based on previous day data
        """

        LOGGER.debug("Getting pivot points for %s" % pair)
        global CROSS_DATA
        func, timeperiod = localconfig
        if (index == None and self.test) or len(self.dataframes[pair]) < 2:
            index = -1
        elif index == None and not self.test:
            index = -2
        # Get current date:
        scheme = {}
        scheme["close_time"] = str(dataframe.iloc[index]["closeTime"])

        # get yesterday's m'epoch time
        get_data_for = int(int(scheme["close_time"]) - 1.728e+8)
        # use human-readable date as dict key
        key = pair + strftime('%Y-%m-%d', localtime(get_data_for/1000))

        if key not in CROSS_DATA:
            # if data doesn't already exist for this date, then wipe previous data and re-fetch data
            # for current date
            CROSS_DATA = {}
            CROSS_DATA[key] = get_all_klines(pair, '1d', get_data_for, 3)

        klines = CROSS_DATA[key]
        result = result = (float(klines[0]['high']) + float(klines[0]['low']) + \
                           float(klines[0]['close']))/3
        scheme["data"] = result
        scheme["symbol"] = pair
        scheme["event"] = "{0}_{1}".format(func, timeperiod)

        self.schemes.append(scheme)
        LOGGER.debug("Done getting pivot")

    @get_exceptions
    def get_tsi(self, pair, dataframe, index=None, localconfig=None):
        """
        Get TSI osscilator
        """
        LOGGER.debug("Getting TSI oscillator for %s" % pair)
        if (index == None and self.test) or len(self.dataframes[pair]) < 2:
            index = -1
        elif index == None and not self.test:
            index = -2

        func, timeperiod = localconfig
        tsi = ta.smi(dataframe.close.astype(float), fast=13, slow=25, signal=13)
        if func == 'tsi':
            result = float(tsi[tsi.columns[0]].iloc[index]) * 100
        elif func == 'signal':
            result = float(tsi[tsi.columns[1]].iloc[index]) * 100
        else:
            raise RuntimeError
        scheme = {}
        scheme["data"] = result
        scheme["symbol"] = pair
        scheme["event"] = "{0}_{1}".format(func, timeperiod)

        scheme["close_time"] = str(self.dataframes[pair].iloc[index]["closeTime"])

        self.schemes.append(scheme)
        LOGGER.debug("Done getting TSI")

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
        if (index == None and self.test) or len(self.dataframes[pair]) < 2:
            index = -1
        elif index == None and not self.test:
            index = -2

        func, timeperiod = localconfig  # split tuple
        LOGGER.debug("Getting %s_%s for %s" % (func, timeperiod, pair))
        scheme = {}
        mine = dataframe.apply(pandas.to_numeric).loc[:index]
        rsi = talib.RSI(dataframe.close.values.astype(float) * 100000, timeperiod=int(timeperiod))
        scheme["symbol"] = pair
        scheme["event"] = "{0}_{1}".format(func, timeperiod)

        scheme["close_time"] = str(self.dataframes[pair].iloc[index]["closeTime"])
        scheme["data"] = rsi[index]

        self.schemes.append(scheme)
        LOGGER.debug("Done getting RSI")

    @get_exceptions
    def get_stochrsi(self, pair, dataframe, index=None, localconfig=None):
        """
        get Stochastic RSI values for given pair
        Append current Stochastic RSI data to instance variable

        Args:
              pair: trading pair (eg. XRPBTC)
              localconfig: indicator config tuple
        Returns:
            k,d

        """
        func, details = localconfig  # split tuple
        timeperiod, k_period, d_period = details.split(',')
        LOGGER.debug("Getting %s_%s for %s" % (func, timeperiod, pair))
        scheme = {}
        mine = dataframe.apply(pandas.to_numeric).loc[:index]
        rsi = talib.RSI(dataframe.close.values.astype(float) * 100000, timeperiod=int(timeperiod))
        rsinp = rsi[numpy.logical_not(numpy.isnan(rsi))]
        stochrsi = talib.STOCH(rsinp, rsinp, rsinp, int(timeperiod), int(k_period), int(d_period))

        scheme["symbol"] = pair
        scheme["event"] = "{0}_{1}".format(func, timeperiod)

        if (index == None and self.test) or len(self.dataframes[pair]) < 2:
            index = -1
        elif index == None and not self.test:
            index = -2
        scheme["close_time"] = str(self.dataframes[pair].iloc[index]["closeTime"])

        #scheme["data"] = stochrsi[index][0]

        scheme["event"] = "{0}_{1}".format(func, timeperiod)
        scheme["data"] = stochrsi[0][index], stochrsi[1][index]
        self.schemes.append(scheme)

        LOGGER.debug("Done getting STOCHRSI")

    @get_exceptions
    def get_envelope(self, pair, dataframe, index=None, localconfig=None):
        """
        Get envelope strategy
        """
        klines = self.__make_data_tupple(dataframe.iloc[:index])
        func, timeperiod = localconfig
        close = klines[-1]
        basis = talib.SMA(close, int(timeperiod))
        percent = 1.1
        k = percent / 100
        upper = basis * (1 + k)
        lower = basis * (1 - k)

        results = {}
        results['upper'] = upper[-1]
        results['middle'] = basis[-1]
        results['lower'] = lower[-1]
        scheme = {}
        try:
            current_price = str(Decimal(self.dataframes[pair].iloc[-1]["close"]))

            scheme["data"] = results[func]
            scheme["symbol"] = pair
            scheme["event"] = func + "_" + str(timeperiod)

            if (index == None and self.test) or len(self.dataframes[pair]) < 2:
                index = -1
            elif index == None and not self.test:
                index = -2
            scheme["close_time"] = str(self.dataframes[pair].iloc[index]["closeTime"])

            self.schemes.append(scheme)

        except KeyError as exc:
            LOGGER.warning("KEY FAILURE in envelope  %s" % str(exc))
        LOGGER.debug("Done getting envelope")

    @get_exceptions
    def get_hma(self, pair, dataframe, index=None, localconfig=None):
        """
        Calculate Hull Moving Average using Weighted Moving Average
        """
        klines = self.__make_data_tupple(dataframe.iloc[:index])
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

            if (index == None and self.test) or len(self.dataframes[pair]) < 2:
                index = -1
            elif index == None and not self.test:
                index = -2
            scheme["close_time"] = str(self.dataframes[pair].iloc[index]["closeTime"])

            self.schemes.append(scheme)

        except KeyError as exc:
            LOGGER.warning("KEY FAILURE in moving averages: %s" % str(exc))

        LOGGER.debug("done getting moving averages")

    @get_exceptions
    def get_vol_moving_averages(self, pair, dataframe, index=None, localconfig=None):
        """
        Get moving averages with and expose volume indicator
        """
        self.get_moving_averages(pair, dataframe, index, localconfig, volume=True)

        scheme = {}
        try:
            scheme["symbol"] = pair
            if (index == None and self.test) or len(self.dataframes[pair]) < 2:
                index = -1
            elif index == None and not self.test:
                index = -2
            scheme["data"] = str(self.dataframes[pair].iloc[index]["volume"])
            scheme["event"] = "volume"
            scheme["close_time"] = str(self.dataframes[pair].iloc[index]["closeTime"])
            self.schemes.append(scheme)

        except KeyError as exc:
            LOGGER.warning("KEY FAILURE in moving averages: %s" % str(exc))

        LOGGER.debug("done getting volume moving averages")

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
        LOGGER.debug("Getting moving averages for %s" % pair)
        klines = self.__make_data_tupple(dataframe.iloc[:index])
        func, timeperiod = localconfig  # split tuple
        new_func = func.strip("_vol") if volume else func
        try:
            close = klines[-1] # numpy.ndarray
            vol = klines[0]
        except Exception as exc:
            LOGGER.warning("FAILED moving averages: %s" % str(exc))
            return
        data = vol if volume else close
        try:
            result = getattr(talib, new_func)(data, int(timeperiod))[-1]
        except Exception as exc:
            LOGGER.warning("Overall Exception getting moving averages: %s" % exc)
            return

        scheme = {}

        result = None if math.isnan(result) else format(float(result), ".20f")
        try:
            scheme["data"] = result
            scheme["symbol"] = pair

            scheme["event"] = func + "_" + str(timeperiod)
            if (index == None and self.test) or len(self.dataframes[pair]) < 2:
                index = -1
            elif index == None and not self.test:
                index = -2

            scheme["close_time"] = str(self.dataframes[pair].iloc[index]["closeTime"])
            self.schemes.append(scheme)

        except KeyError as exc:
            LOGGER.warning("KEY FAILURE in moving averages: %s " % str(exc))

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
        LOGGER.debug("Getting Oscillators for %s" % pair)
        klines = self.__make_data_tupple(dataframe.iloc[:index])
        _, open, high, low, close = klines
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

            klines = []
            for i in attrs["klines"]:
                klines.append(locals()[i])

            fastk, fastd = getattr(talib, func)(high, low, close, int(timeperiod))

        except Exception as error:
            traceback.print_exc()
            LOGGER.warning("failed getting oscillators: %s" % str(error))
            return

        result = fastk[-1]
        try:
            scheme["data"] = result
            scheme["symbol"] = pair
            scheme["event"] = '{}_{}'.format(func, timeperiod)

            if (index == None and self.test) or len(self.dataframes[pair]) < 2:
                index = -1
            elif index == None and not self.test:
                index = -2
            scheme["close_time"] = str(self.dataframes[pair].iloc[index]["closeTime"])

            self.schemes.append(scheme)

        except KeyError as error:
            LOGGER.warning("Key failure while getting oscillators: %s" % str(error))
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
        klines = self.__make_data_tupple(dataframe.iloc[:index])
        LOGGER.debug("Getting Indicators for %s" % pair)
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

        if (index == None and self.test) or len(self.dataframes[pair]) < 2:
            index = -1
        elif index == None and not self.test:
            index = -2
        scheme["close_time"] = str(self.dataframes[pair].iloc[index]["closeTime"])

        self.schemes.append(scheme)

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
        LOGGER.debug("Getting supertrend for %s" % pair)
        scheme = {}
        dataframe = self.__renamed_dataframe_columns(dataframe)

        mine = dataframe.apply(pandas.to_numeric).loc[:index]
        timeframe, multiplier = timef.split(',')
        supertrend = SuperTrend(mine, int(timeframe), int(multiplier))
        df_list = supertrend["ST_{0}_{1}".format(timeframe, multiplier)].tolist()
        scheme["data"] = df_list[-1]
        scheme["symbol"] = pair
        scheme["event"] = "STX_{0}".format(timeframe)

        if (index == None and self.test) or len(self.dataframes[pair]) < 2:
            index = -1
        elif index == None and not self.test:
            index = -2
        scheme["close_time"] = str(self.dataframes[pair].iloc[index]["closeTime"])

        self.schemes.append(scheme)
        LOGGER.debug("done getting supertrend")
