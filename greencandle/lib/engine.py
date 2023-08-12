#pylint: disable=no-member,consider-iterating-dictionary,broad-except,too-many-locals
#pylint: disable=global-statement,singleton-comparison,unused-variable

"""
Module for collecting price data and creating TA results
"""

import math
import traceback
import operator
from time import time, strftime, localtime
from concurrent.futures import ProcessPoolExecutor
from collections import defaultdict
from decimal import Decimal
import pandas
import numpy
import pandas_ta as ta
import talib

from greencandle.lib.common import make_float
from greencandle.lib.binance_common import get_all_klines
from greencandle.lib.logger import get_logger, exception_catcher

LOGGER = get_logger(__name__)
CROSS_DATA = {}  # data from different time period

class Engine(dict):
    """ Represent events created from data & indicators """

    get_exceptions = exception_catcher((Exception))
    def __init__(self, dataframes, interval=None, test=False, redis=None):
        """
        Initialize class
        Create hold and event dicts
        Fetch initial data from binance and store within object
        """
        LOGGER.debug("Fetching raw data")
        self.interval = interval
        self.pairs = [key for key in dataframes.keys() if len(dataframes[key]) > 4]
        self.test = test
        self.redis = redis
        self["hold"] = {}
        self["event"] = {}
        self.current_time = str(int(time()*1000))
        self.dataframes = dataframes

        self.schemes = []
        super().__init__()
        LOGGER.debug("Finished fetching raw data")

    def __make_data_tupple(self, pair, index):
        """
        Transform dataframe to tupple of of floats
        """
        local = self.dataframes[pair] if index == -1 else self.dataframes[pair].iloc[:index]
        ohlc = (make_float(local.volume),
                make_float(local.open),
                make_float(local.high),
                make_float(local.low),
                make_float(local.close))
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
        final_scheme = defaultdict(lambda: defaultdict(dict))
        for scheme in self.schemes:
            pair = scheme["symbol"]
            # add to redis
            event = scheme['event']
            open_time = str(self.dataframes[pair].iloc[-1]["openTime"]) if not "open_time" in \
                    scheme else scheme["open_time"]

            result = None if (isinstance(scheme["data"], float) and
                              math.isnan(scheme["data"])) else scheme["data"]
            final_scheme[pair][open_time][event] = result

        for pair, data in final_scheme.items():
            self.redis.add_data(pair, self.interval, data)

        self.schemes = []

    @get_exceptions
    def get_data(self, localconfig=None, first_run=False, no_of_runs=999):
        """
        Iterate through data and trading pairs to extract data
        Run data through indicator, oscillators, moving average
        Return dict containing alert data and hold data

        Args: None

        Returns:
            dict containing all collected data
        """

        # get indicators supertrend, and API for each trading pair
        pool = ProcessPoolExecutor(max_workers=20)
        futures = []

        for pair in self.pairs:
            pair = pair.strip()
            actual_klines = len(self.dataframes[pair])

            futures.append(pool.submit(getattr(self,'send_ohlcs')(pair, first_run=first_run,
                                                                  no_of_runs=no_of_runs)))

            for item in localconfig:
                function, name, period = item.split(';')
                # call each method defined in config with current pair and name,period tuple
                # from config eg. self.supertrend(pair, config), where config is a tuple
                # each method has the method name in 'function't st

                if first_run:
                    for seq in range(int(actual_klines))[-no_of_runs:]:
                        if seq > len(self.dataframes[pair]):
                            continue
                        futures.append(pool.submit(getattr(self, function)(pair, index=seq,
                                                            localconfig=(name, period))))
                else:
                    futures.append(pool.submit(getattr(self, function)(pair, index=None,
                                                        localconfig=(name, period))))
        pool.shutdown(wait=False)
        self.__add_schemes()

        LOGGER.debug("Done getting data")
        return self

    def send_ohlcs(self, pair, first_run, no_of_runs=999):
        """Send ohcls data to redis"""
        scheme = {}
        scheme["symbol"] = pair
        # Unless we are in test mode, use the second to last data row as the previous one is still
        # being constructed and contains incomplete data

        self.schemes.append(scheme)
        if first_run:
            for seq in range(-no_of_runs, 0, 1): # last x items in seq order
                LOGGER.debug("Getting initial sequence number %s", seq)
                scheme['data'] = self.dataframes[pair].iloc[seq].to_dict()
                for key, val in scheme['data'].items():
                    if isinstance(val, numpy.int64):
                        scheme['data'][key] = int(val)
                scheme["event"] = "ohlc"
                scheme["open_time"] = str(self.dataframes[pair].iloc[seq]["openTime"])
                self.schemes.append(scheme)

                # reset for next loop
                scheme = {"symbol": pair, "event": "ohlc"}

        location = -1
        try:
            close = float(self.dataframes[pair].iloc[location]["close"])
            if close <= 0:
                LOGGER.critical("Zero size dataframe found")
        except Exception:
            LOGGER.critical("Non-float dataframe found")

        scheme['data'] = self.dataframes[pair].iloc[location].to_dict()
        for key, val in scheme['data'].items():
            if isinstance(val, numpy.int64):
                scheme['data'][key] = int(val)

        scheme["event"] = "ohlc"
        scheme["open_time"] = str(self.dataframes[pair].iloc[location]["openTime"])
        self.schemes.append(scheme)

    def get_bb_perc_ema(self, pair, index=None, localconfig=None):
        """
        Get EMA of bbperc
        """
        self.get_bb_perc(pair, index, localconfig, ema=True)

    def get_bb_perc(self, pair, index=None, localconfig=None, ema=False):
        """get bb %"""
        if index is None:
            index = -1
        open_time = str(self.dataframes[pair].iloc[index]["openTime"])
        func, timef = localconfig  # split tuple
        timeframe, multiplier = timef.split(',')

        try:
            if index == -1:
                closes = make_float(self.dataframes[pair].close)
            else:
                closes = make_float(self.dataframes[pair].close.iloc[:index])
            current_price = str(Decimal(self.dataframes[pair].iloc[index]["close"]))
            upper, _, lower = \
                     talib.BBANDS(closes*100000, timeperiod=int(timeframe),
                                  nbdevup=float(multiplier), nbdevdn=float(multiplier), matype=0)

            #%B = (Current Price - Lower Band) / (Upper Band - Lower Band)
            perc = ((float(current_price)- float(lower[-1]/100000)) /
                    (float(upper[-1])/100000 - float(lower[-1])/100000))
            if ema:
                percs = []
                for i in range(-21, 0):

                    # loop over last 21 bb items and get corresponding bbperc
                    current_perc = ((float(current_price) - float(lower[i])/100000) /
                                    (float(upper[i])/100000 - float(lower[i])/100000))
                    percs.append(float(current_perc))
                # convert real list to ndarray
                perc_arr = numpy.array(percs)
                # get EMA using 21 timepeiod
                ema_result = int(talib.EMA(perc_arr, timeperiod=21)[-1])
            else:
                ema_result = None

        except Exception as exc:
            perc = None
            ema_result = None
            LOGGER.debug("Overall Exception getting bb perc: %s seq: %s", exc, index)
        scheme = {}
        try:
            scheme["data"] = ema_result if ema else perc
            scheme["symbol"] = pair
            scheme["event"] = f"{func}_{timeframe}"
            scheme["open_time"] = open_time

            self.schemes.append(scheme)

        except KeyError as exc:
            LOGGER.warning("KEY FAILURE in bb perc : %s", str(exc))

        LOGGER.debug("Done Getting bb perc for %s - %s", pair, open_time)

    def get_bb(self, pair, index=None, localconfig=None):
        """get bollinger bands"""
        if index is None:
            index = -1

        open_time = str(self.dataframes[pair].iloc[index]["openTime"])
        klines = self.__make_data_tupple(pair, index)

        func, timef = localconfig  # split tuple
        timeframe, multiplier = timef.split(',')
        try:
            close = klines[-1]

        except Exception as exc:
            LOGGER.info("FAILED bbands: %s ", str(exc))
            return
        try:
            upper, middle, lower = \
                    talib.BBANDS(close * 100000, timeperiod=int(timeframe),
                                 nbdevup=float(multiplier), nbdevdn=float(multiplier), matype=0)
            res = [upper[-1]/100000, middle[-1]/100000, lower[-1]/100000]

        except Exception as exc:
            res = [None, None, None]
            LOGGER.debug("Overall Exception getting bollinger bands: %s seq: %s", exc, index)
        try:
            scheme = {}
            scheme["open_time"] = open_time
            scheme["data"] = res
            scheme["symbol"] = pair
            scheme["event"] = f"{func}_{timeframe}"
            self.schemes.append(scheme)

        except KeyError as exc:
            LOGGER.warning("KEY FAILURE in bollinger bands: %s", str(exc))

        LOGGER.debug("Done Getting bb for %s - %s", pair, open_time)

    @get_exceptions
    def get_pivot(self, pair, index=None, localconfig=None):
        """
        Get pivot points based on previous day data
        !!!Does not work with test data!!!
        """

        global CROSS_DATA
        func, timeperiod = localconfig
        index = -1
        # Get current date:
        scheme = {}
        scheme["open_time"] = str(self.dataframes[pair].iloc[index]["openTime"])

        # get yesterday's m'epoch time
        get_data_for = int(int(scheme["open_time"]) - 1.728e+8)
        # use human-readable date as dict key
        key = pair + strftime('%Y-%m-%d', localtime(get_data_for/1000))

        if key not in CROSS_DATA:
            # if data doesn't already exist for this date, then wipe previous data and re-fetch data
            # for current date
            CROSS_DATA = {}
            CROSS_DATA[key] = get_all_klines(pair, '1d', get_data_for, 3)

        klines = CROSS_DATA[key]
        result = (float(klines[0]['high']) + float(klines[0]['low']) + float(klines[0]['close']))/3
        scheme["data"] = result
        scheme["symbol"] = pair
        scheme["event"] = f"{func}_{timeperiod}"

        self.schemes.append(scheme)
        LOGGER.debug("Done Getting pivot for %s - %s", pair, scheme['open_time'])

    @get_exceptions
    def get_tsi(self, pair, index=None, localconfig=None):
        """
        Get TSI osscilator
        """
        index = -1
        func, timeperiod = localconfig
        tsi = ta.smi(self.dataframes[pair].close.astype(float), fast=13, slow=25, signal=13)
        if func == 'tsi':
            result = float(tsi[tsi.columns[0]].iloc[index]) * 100
        elif func == 'signal':
            result = float(tsi[tsi.columns[1]].iloc[index]) * 100
        else:
            raise RuntimeError
        scheme = {}
        scheme["data"] = result
        scheme["symbol"] = pair
        scheme["event"] = f"{func}_{timeperiod}"

        scheme["open_time"] = str(self.dataframes[pair].iloc[index]["openTime"])

        self.schemes.append(scheme)
        LOGGER.debug("Done Getting TSI for %s - %s", pair, scheme['open_time'])

    @get_exceptions
    def get_atr(self, pair, index=None, localconfig=None):
        """
        get Average True Range values for given pair
        Append current RSI data to instance variable

        Args:
              pair: trading pair (eg. XRPBTC)
              localconfig: indicator config tuple
        Returns:
            None

        """

        func, timeperiod = localconfig  # split tuple
        scheme = {}
        if index is None:
            index = -1
        atr = talib.ATR(high=self.dataframes[pair].high.values.astype(float),
                        low=self.dataframes[pair].low.values.astype(float),
                        close=self.dataframes[pair].close.values.astype(float), timeperiod=14)
        scheme["symbol"] = pair
        scheme["event"] = f"{func}_{timeperiod}"
        scheme["open_time"] = str(self.dataframes[pair].iloc[index]["openTime"])
        scheme["data"] = float(atr[index]) if atr[index] != None else None
        self.schemes.append(scheme)
        LOGGER.debug("Done Getting ATR for %s - %s", pair, scheme['open_time'])

    @get_exceptions
    def get_rsi(self, pair, index=None, localconfig=None):
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
        scheme = {}

        if index is None:
            index = -1
        rsi = talib.RSI(self.dataframes[pair].close.values.astype(float) * 100000,
                        timeperiod=int(timeperiod))
        scheme["symbol"] = pair
        scheme["event"] = f"{func}_{timeperiod}"

        scheme["open_time"] = str(self.dataframes[pair].iloc[index]["openTime"])
        scheme["data"] = float(rsi[index]) if rsi[index] != None else None

        self.schemes.append(scheme)
        LOGGER.debug("Done Getting RSI for %s - %s", pair, scheme['open_time'])

    @get_exceptions
    def get_stochrsi(self, pair, index=None, localconfig=None):
        """
        get Stochastic RSI values for given pair
        Append current Stochastic RSI data to instance variable

        Args:
              pair: trading pair (eg. XRPBTC)
              localconfig: indicator config tuple
        Returns:
            k,d

        """

        series = self.dataframes[pair].close.apply(pandas.to_numeric).astype('float32')

        if index is None:
            index = -1
        else:
            series = series.iloc[:index +1]
        func, details = localconfig  # split tuple
        rsi_period, stoch_period, smooth = (int(x) for x in details.split(','))

        scheme = {}
        try:
            # Calculate RSI
            delta = series.astype('float32').diff().dropna()
            ups = delta * 0
            downs = ups.copy()
            ups[delta > 0] = delta[delta > 0]
            downs[delta < 0] = -delta[delta < 0]
            #first value is sum of avg gains
            ups[ups.index[rsi_period-1]] = numpy.mean(ups[:rsi_period])
            ups = ups.drop(ups.index[:(rsi_period-1)])
            #first value is sum of avg losses
            downs[downs.index[rsi_period-1]] = numpy.mean(downs[:rsi_period])
            downs = downs.drop(downs.index[:(rsi_period-1)])
            r_s = ups.ewm(com=rsi_period-1, min_periods=0, adjust=False, ignore_na=False).mean() / \
                 downs.ewm(com=rsi_period-1, min_periods=0, adjust=False, ignore_na=False).mean()
            rsi = 100 - 100 / (1 + r_s)

            # Calculate StochRSI
            stochrsi = (rsi - rsi.rolling(stoch_period, min_periods=0).min()) / \
            (rsi.rolling(stoch_period, min_periods=0).max() - rsi.rolling(stoch_period,
                                                                          min_periods=0).min())
            stochrsik = stochrsi.rolling(smooth, min_periods=0).mean()
            stochrsid = stochrsik.rolling(smooth, min_periods=0).mean()
            sto_k = 100 * stochrsik
            sto_d = 100 * stochrsid

            scheme["symbol"] = pair
            scheme["event"] = f"{func}_{rsi_period}"
            scheme["open_time"] = str(self.dataframes[pair].iloc[index]["openTime"])
            scheme["data"] = sto_k.iloc[-1], sto_d.iloc[-1]
            self.schemes.append(scheme)

        except (IndexError, KeyError) as exc:
            LOGGER.warning("FAILURE in stochrsi %s", str(exc))
        else:
            LOGGER.debug("Done Getting STOCHRSI for %s - %s", pair, scheme['open_time'])

    @get_exceptions
    def get_envelope(self, pair, index=None, localconfig=None):
        """
        Get envelope strategy
        """
        klines = self.__make_data_tupple(pair, index)
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
            scheme["data"] = results[func]
            scheme["symbol"] = pair
            scheme["event"] = f"{func}_{timeperiod}"
            index = -1
            scheme["open_time"] = str(self.dataframes[pair].iloc[index]["openTime"])
            self.schemes.append(scheme)

        except KeyError as exc:
            LOGGER.warning("KEY FAILURE in envelope  %s", str(exc))
        LOGGER.debug("Done Getting envelope for %s - %s", pair, scheme['open_time'])

    @get_exceptions
    def get_hma(self, pair, index=None, localconfig=None):
        """
        Calculate Hull Moving Average using Weighted Moving Average
        """
        klines = self.__make_data_tupple(pair, index)
        func, timeperiod = localconfig
        close = klines[-1]
        first = talib.WMA(close, int(timeperiod)/2)
        second = talib.WMA(close, int(timeperiod))

        result = talib.WMA((2 * first) - second, round(math.sqrt(int(timeperiod))))[-1]
        if result > close[-1]:
            trigger = "SELL"
        else:
            trigger = "BUY"
        scheme = {}
        try:
            scheme["data"] = result
            scheme["symbol"] = pair
            scheme["event"] = f"{func}_{timeperiod}"

            index = -1
            scheme["open_time"] = str(self.dataframes[pair].iloc[index]["openTime"])

            self.schemes.append(scheme)

        except KeyError as exc:
            LOGGER.warning("KEY FAILURE in moving averages: %s", str(exc))

        LOGGER.debug("Done Getting MA for %s - %s", pair, scheme['open_time'])

    @get_exceptions
    def get_moving_averages(self, pair, index=None, localconfig=None):
        """
        Apply moving averages to klines and get BUY/SELL triggers
        Add data to DB

        Args:
            pair: trading pair (eg. XRPBTC)
            localconfig: indicator config tuple

        Returns:
            None
        """
        if index is None:
            index = -1
        open_time = str(self.dataframes[pair].iloc[index]["openTime"])
        klines = self.__make_data_tupple(pair, index)
        func, timef = localconfig  # split tuple
        results = {}

        try:
            if index == -1:
                closes = make_float(self.dataframes[pair].close)
            else:
                closes = make_float(self.dataframes[pair].close.iloc[:index])

            results = talib.EMA(closes, timeperiod=int(timef))

        except Exception as exc:
            LOGGER.debug("Overall Exception getting EMA: %s seq: %s", exc, index)
        scheme = {}
        try:

            scheme["data"] = results[-1]
            scheme["symbol"] = pair
            scheme["event"] = "{0}_{1}".format(func, timef)
            scheme["open_time"] = open_time

            self.schemes.append(scheme)

        except KeyError as exc:
            LOGGER.warning("KEY FAILURE in moving averages : %s", str(exc))

        LOGGER.debug("Done Getting moving averages for %s - %s", pair, open_time)

    @get_exceptions
    def get_oscillators(self, pair, index=None, localconfig=None):
        """

        Apply osscilators to klines and get BUY/SELL triggers
        Add data to DB

        Args:
            pair: trading pair (eg. XRPBTC)
            localconfig: indicator config tuple

        Returns:
            None
        """
        klines = self.__make_data_tupple(pair, index)
        _, _, high, low, close = klines
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
        attrs = trends[func]
        try:

            klines = []
            for i in attrs["klines"]:
                klines.append(locals()[i])

            fastk, _ = getattr(talib, func)(high, low, close, int(timeperiod))

        except Exception as error:
            traceback.print_exc()
            LOGGER.debug("failed getting oscillators: %s", str(error))
            return

        result = float(fastk[-1]) if fastk[-1] != None else None
        try:
            scheme["data"] = result
            scheme["symbol"] = pair
            scheme["event"] = f'{func}_{timeperiod}'
            index = -1
            scheme["open_time"] = str(self.dataframes[pair].iloc[index]["openTime"])
            self.schemes.append(scheme)

        except KeyError as error:
            LOGGER.warning("Key failure while getting oscillators: %s", str(error))
        LOGGER.debug("Done Getting oscillators for %s - %s", pair, scheme['open_time'])

    @get_exceptions
    def get_indicators(self, pair, index=None, localconfig=None):
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
        klines = self.__make_data_tupple(pair, index)
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
        scheme["event"] = f"{func}_{timeperiod}"

        index = -1
        scheme["open_time"] = str(self.dataframes[pair].iloc[index]["openTime"])
        self.schemes.append(scheme)
        LOGGER.debug("Done Getting indicators for %s - %s", pair, scheme['open_time'])

    @get_exceptions
    def get_ha(self, pair, index=None, localconfig=None):
        """
        Get Heikin-Ashi candles

        Args:
              pair: trading pair (eg. XRPBTC)
        Returns:
            None

        """
        dataframe = self.__renamed_dataframe_columns(self.dataframes[pair])
        series = dataframe.apply(pandas.to_numeric)
        if index is None:
            index = -1
        else:
            # line up with TV graphs
            series = series.iloc[:index +1]
        scheme = {}
        hashi = ta.ha(open_=series.Open.astype(float),
                      high=series.High.astype(float),
                      low=series.Low.astype(float),
                      close=series.Close.astype(float)
                      )
        scheme["data"] = (hashi['HA_open'].iloc[-1], hashi['HA_high'].iloc[-1],
                          hashi['HA_low'].iloc[-1], hashi['HA_close'].iloc[-1])
        scheme["symbol"] = pair
        scheme["event"] = "ha"
        scheme["open_time"] = str(self.dataframes[pair].iloc[index]["openTime"])

        self.schemes.append(scheme)
        LOGGER.debug("Done Getting haikin ashi for %s - %s", pair, scheme['open_time'])

    @get_exceptions
    def get_supertrend(self, pair, index=None, localconfig=None):
        """
        Get the super trend oscillator values for a given pair
        append current supertrend data to instance variable

        Args:
              pair: trading pair (eg. XRPBTC)
              localconfig: indicator config tuple
        Returns:
            None

        """
        dataframe = self.__renamed_dataframe_columns(self.dataframes[pair])
        series = dataframe.apply(pandas.to_numeric)
        if index is None:
            index = -1
        else:
            # line up with TV graphs
            series = series.iloc[:index +1]
        _, timef = localconfig  # split tuple
        scheme = {}
        timeframe, multiplier = timef.split(',')
        supertrend2 = ta.supertrend(high=series.High.astype(float),
                                    low=series.Low.astype(float),
                                    close=series.Close.astype(float),
                                    multiplier=float(multiplier), length=float(timeframe))
        # -1 = downtrend - go short
        # 1 = uptrend - go long
        scheme["data"] = (int(supertrend2[f'SUPERTd_{timeframe}_{multiplier}.0'].iloc[-1]),
                          supertrend2[f'SUPERT_{timeframe}_{multiplier}.0'].iloc[-1])
        scheme["symbol"] = pair
        scheme["event"] = f"STX_{timeframe}"
        scheme["open_time"] = str(self.dataframes[pair].iloc[index]["openTime"])

        self.schemes.append(scheme)
        LOGGER.debug("Done Getting supertrend for %s - %s", pair, scheme['open_time'])
