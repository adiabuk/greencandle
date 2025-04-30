#pylint: disable=no-member,consider-iterating-dictionary,broad-except,too-many-locals
#pylint: disable=global-statement,singleton-comparison,unused-argument,unused-variable

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
from scipy.stats import linregress
from greencandle.lib.common import make_float
from greencandle.lib.binance_common import get_all_klines
from greencandle.lib.logger import get_logger, exception_catcher
from greencandle.lib.web import decorator_timer

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
        LOGGER.debug("fetching raw data")
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
        LOGGER.debug("finished fetching raw data")

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
    @decorator_timer
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

        LOGGER.debug("done getting data")
        return self

    @staticmethod
    def get_slope(array):
        """
        given a list of values fetch and return the slope of the line
        Input can be a list or an array
        Output is a numpy array
        """
        y = numpy.array(array)
        x = numpy.arange(len(y))
        slope, intercept, r_value, p_value, std_err = linregress(x,y)
        return slope


    @decorator_timer
    def send_ohlcs(self, pair, first_run, no_of_runs=999):
        """Send ohcls data to redis"""
        scheme = {}
        scheme["symbol"] = pair
        # Unless we are in test mode, use the second to last data row as the previous one is still
        # being constructed and contains incomplete data

        self.schemes.append(scheme)
        if first_run:
            for seq in range(-no_of_runs, 0, 1): # last x items in seq order
                LOGGER.debug("getting initial sequence number %s", seq)
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
                LOGGER.critical("zero size dataframe found")
                return
        except Exception:
            LOGGER.critical("non-float dataframe found")
            return

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

    def get_macd(self, pair, index=None, localconfig=None):
        """ get macd """

        if index is None:
            index = -1
        func, timef = localconfig  # split tuple
        short_term, long_term, signal_period = timef.split(',')
        # Calculate macd

        # Calculate short-term and long-term EMAs
        short_ema = self.dataframes[pair]['close'].ewm(span=int(short_term), adjust=False).mean()
        long_ema = self.dataframes[pair]['close'].ewm(span=int(long_term), adjust=False).mean()

        # Calculate macd Line
        macd_line = short_ema - long_ema

        # Calculate Signal Line
        signal_line = macd_line.ewm(span=int(signal_period), adjust=False).mean()

        # Calculate macd Histogram
        macd_histogram = macd_line - signal_line

        scheme = {}
        try:
            scheme["data"] = (macd_line.iloc[index], signal_line.iloc[index],
                              macd_histogram.iloc[index])
            scheme["symbol"] = pair
            scheme["event"] = f"{func}_{short_term}"
            open_time = str(self.dataframes[pair].iloc[index]["openTime"])
            scheme["open_time"] = open_time

            self.schemes.append(scheme)

        except Exception as exc:
            LOGGER.warning("overall failure in macd: %s", str(exc))
            return

        LOGGER.debug("done getting macd for %s - %s: %s", pair, scheme['open_time'], scheme['data'])

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
            LOGGER.debug("overall Exception getting bb perc: %s seq: %s", exc, index)
            return
        scheme = {}
        try:
            scheme["data"] = ema_result if ema else perc
            scheme["symbol"] = pair
            scheme["event"] = f"{func}_{timeframe}"
            scheme["open_time"] = open_time

            self.schemes.append(scheme)

        except KeyError as exc:
            LOGGER.warning("key failure In bb perc : %s", str(exc))
            return

        LOGGER.debug("done getting bb perc for %s - %s", pair, open_time)

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
            LOGGER.info("failed Bbands: %s ", str(exc))
            return
        try:
            upper, middle, lower = \
                    talib.BBANDS(close * 100000, timeperiod=int(timeframe),
                                 nbdevup=float(multiplier), nbdevdn=float(multiplier), matype=0)
            res = [upper[-1]/100000, middle[-1]/100000, lower[-1]/100000]

        except Exception as exc:
            res = [None, None, None]
            LOGGER.debug("overall Exception getting bollinger bands: %s seq: %s", exc, index)
            return
        try:
            scheme = {}
            scheme["open_time"] = open_time
            scheme["data"] = res
            scheme["symbol"] = pair
            scheme["event"] = f"{func}_{timeframe}"
            self.schemes.append(scheme)

        except KeyError as exc:
            LOGGER.warning("key failure in bollinger bands: %s", str(exc))
            return

        LOGGER.debug("done getting bb for %s - %s", pair, open_time)

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
        LOGGER.debug("done getting pivot for %s - %s", pair, scheme['open_time'])

    @get_exceptions
    def get_cci(self, pair, index=None, localconfig=None):
        """
        Get CCI osscilator
        """
        try:
            if index is None:
                index = -1
            func, timeperiod = localconfig
            cci = ta.cci(self.dataframes[pair].high.astype(float),
                         self.dataframes[pair].low.astype(float),
                         self.dataframes[pair].close.astype(float),
                         length=float(timeperiod))
            scheme = {}
            result = float(cci.iloc[index])
            scheme["data"] = result
            scheme["symbol"] = pair
            scheme["event"] = f"{func}_{timeperiod}"

            scheme["open_time"] = str(self.dataframes[pair].iloc[index]["openTime"])

            self.schemes.append(scheme)

        except (IndexError, KeyError, AttributeError) as exc:
            LOGGER.debug("failure In cci %s for pair %s", str(exc), pair)
            return
        LOGGER.debug("done getting cci For %s - %s", pair, scheme['open_time'])

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
        LOGGER.debug("done getting tsi For %s - %s", pair, scheme['open_time'])

    def get_atr_perc(self, pair, index=None, localconfig=None):
        """
        Get ATR percentage
        """

        def williams_ma(data, period):
            """
            Williams moving average
            """
            data = pandas.DataFrame(data)
            return data.rolling(period).apply(lambda x: ((numpy.arange(period)+1)*x).sum()/( \
                    numpy.arange(period)+1).sum(), raw=True)

        def hull_ma(data, period):
            """
            Hull moving average
            """
            data = pandas.DataFrame(data)
            return williams_ma(williams_ma(data, period//2).multiply(2).sub(williams_ma(data,
                                                                                        period)),
                               int(numpy.sqrt(period)))

        func, timef = localconfig  # split tuple
        length, lookback = timef.split(',')

        scheme = {}
        if index is None:
            index = -1
            data = talib.TRANGE(high=self.dataframes[pair].high.values.astype(float),
                              low=self.dataframes[pair].low.values.astype(float),
                              close=self.dataframes[pair].close.values.astype(float))
        else:
            data = talib.TRANGE(high=self.dataframes[pair].high.values.astype(float)[:index +1],
                              low=self.dataframes[pair].low.values.astype(float)[:index +1],
                              close=self.dataframes[pair].close.values.astype(float)[:index +1])


        atrpercent = hull_ma(data, int(length))

        col_one_list = atrpercent[0].tolist()[-int(lookback)+1:]
        current = col_one_list.pop()
        count = 0
        for item in col_one_list:
            if item <= current:
                count +=1

        rank = 100 * count / int(lookback)


        scheme["symbol"] = pair
        scheme["event"] = f"{func}_{length}"
        scheme["open_time"] = str(self.dataframes[pair].iloc[index]["openTime"])
        scheme["data"] = rank
        self.schemes.append(scheme)
        LOGGER.debug("done getting atr rankfor %s - %s", pair, scheme['open_time'])

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
        atr_ema = talib.EMA(atr, timeperiod=50)
        scheme["symbol"] = pair
        scheme["event"] = f"{func}_{timeperiod}"
        scheme["open_time"] = str(self.dataframes[pair].iloc[index]["openTime"])
        scheme["data"] = (float(atr[index]), float(atr_ema[-1])) if atr[index] != None else (None,
                                                                                             None)
        self.schemes.append(scheme)
        LOGGER.debug("done getting atr For %s - %s", pair, scheme['open_time'])

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
        LOGGER.debug("done getting rsi For %s - %s", pair, scheme['open_time'])

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
            LOGGER.warning("failure In stochrsi %s", str(exc))
            return
        LOGGER.debug("done getting stochrsi For %s - %s", pair, scheme['open_time'])

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
            LOGGER.warning("key failure In envelope  %s", str(exc))
            return
        LOGGER.debug("done getting envelope for %s - %s", pair, scheme['open_time'])

    @get_exceptions
    def get_hma(self, pair, index=None, localconfig=None):
        """
        Calculate Hull Moving Average using Weighted Moving Average
        """
        klines = self.__make_data_tupple(pair, index)
        func, timeperiod = localconfig
        close = klines[-1]
        first = talib.williams_ma(close, int(timeperiod)/2)
        second = talib.williams_ma(close, int(timeperiod))

        result = talib.williams_ma((2 * first) - second, round(math.sqrt(int(timeperiod))))[-1]
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
            LOGGER.warning("key failure In moving averages: %s", str(exc))
            return

        LOGGER.debug("done getting ma for %s - %s", pair, scheme['open_time'])

    @get_exceptions
    def get_smi(self, pair, index=None, localconfig=None):
        """
        Stochastic Momementum Index with EMA
        """
        def ema_ema(source, length):
            ema1 = source.ewm(span=length, adjust=False).mean()
            return ema1.ewm(span=length, adjust=False).mean()

        scheme = {}
        if index is None:
            index = -1
        func, timef = localconfig  # split tuple
        length_k, length_d, length_ema = timef.split(',')

        highest_high = self.dataframes[pair].high.rolling(int(length_k)).max()
        lowest_low = self.dataframes[pair].low.rolling(int(length_k)).min()
        highest_lowest_range = highest_high - lowest_low
        relative_range = self.dataframes[pair].close.astype(float) - (highest_high + lowest_low) / 2

        smi = 200 * (ema_ema(relative_range, int(length_d)) / ema_ema(highest_lowest_range,
                                                                 int(length_d)))
        smi_ema = smi.ewm(span=int(length_ema), adjust=False).mean()

        smi_df = pandas.DataFrame({
            'SMI': smi,
            'SMI_EMA': smi_ema
        })

        try:
            scheme["data"] = tuple(smi_df.iloc[index])
            scheme["symbol"] = pair
            scheme["event"] = f"{func}_{length_k}"
            scheme["open_time"] = str(self.dataframes[pair].iloc[index]["openTime"])

            self.schemes.append(scheme)

        except KeyError as exc:
            LOGGER.warning("key failure getching smi: %s", str(exc))
            return

        LOGGER.debug("done getting smi for %s - %s", pair, scheme['open_time'])

    @get_exceptions
    def get_recent_highlow(self, pair, index=None, localconfig=None):
        """
        Get recent high and low in past x candles
        """
        scheme = {}
        func, timef = localconfig  # split tuple
        if index is None:
            index = -1

        recent_high = self.dataframes[pair].high.tail(int(timef)).max()
        recent_low = self.dataframes[pair].low.tail(int(timef)).min()

        try:
            scheme["data"] = recent_high, recent_low
            scheme["symbol"] = pair
            scheme["event"] = f"{func}_{timef}"
            scheme["open_time"] = str(self.dataframes[pair].iloc[index]["openTime"])

            self.schemes.append(scheme)

        except KeyError as exc:
            LOGGER.warning("key failure getching recent high/low: %s", str(exc))
            return

        LOGGER.debug("done getting recent high/low for %s - %s", pair, scheme['open_time'])

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
            LOGGER.debug("overall exception getting ema: %s seq: %s", exc, index)
            return
        scheme = {}
        try:
            slope = self.get_slope(results[-6:])
            scheme["data"] = results[-1], slope
            scheme["symbol"] = pair
            scheme["event"] = f"{func}_{timef}"
            scheme["open_time"] = open_time

            self.schemes.append(scheme)

        except KeyError as exc:
            LOGGER.warning("key failure in moving averages : %s", str(exc))
            return

        LOGGER.debug("done getting moving averages for %s - %s", pair, open_time)

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
            LOGGER.warning("key failure while getting oscillators: %s", str(error))
            return
        LOGGER.debug("done getting oscillators for %s - %s", pair, scheme['open_time'])

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
        trends = {"HAMMER": {100: "BUY", 0:"HODL"},
                  "INVERTEDHAMMER": {100: "SELL", 0:"HODL"},
                  "ENGULFING": {-100:"SELL", 100:"BUY", 0:"HODL"},
                  "MORNINGSTAR": {-100:"SELL", 100:"BUY", 0:"HODL"},
                  "SHOOTINGSTAR": {-100:"SELL", 100:"BUY", 0:"HODL"},
                  "SPINNINGTOP": {-100:"SELL", 100:"BUY", 0:"HODL"},
                  "MARUBOZU": {-100:"SELL", 100:"BUY", 0:"HODL"},
                  "DOJI": {100: "HODL", 0:"HODL"}}

        result = getattr(talib, "CDL" + func)(*klines).tolist()[-1]

        scheme["data"] = result   # convert from array to list
        scheme["symbol"] = pair
        scheme["event"] = f"{func}_{timeperiod}"

        index = -1
        scheme["open_time"] = str(self.dataframes[pair].iloc[index]["openTime"])
        self.schemes.append(scheme)
        LOGGER.debug("done getting indicators for %s - %s", pair, scheme['open_time'])

    @get_exceptions
    def get_ha(self, pair, index=None, localconfig=None):
        """
        Get Heikin-Ashi candles

        Args:
              pair: trading pair (eg. XRPBTC)
        Returns:
            None

        """

        func, timef = localconfig  # split tuple
        dataframe = self.__renamed_dataframe_columns(self.dataframes[pair])
        if index:
            series = dataframe.apply(pandas.to_numeric)[:index+1].astype(float)
        else:
            series = dataframe.apply(pandas.to_numeric).astype(float)
        scheme = {}
        series['HA_Close']=(series.Open + series.High + series.Low + series.Close)/4

        series.reset_index(inplace=True)

        ha_open = [ (series.Open[0] + series.Close[0]) / 2 ]

        for i in range(0, len(series)-1):
            ha_open.append((ha_open[i] + series.HA_Close.values[i]) / 2)
        series['HA_Open'] = ha_open

        series.set_index('index', inplace=True)

        series['HA_High']=series[['HA_Open','HA_Close','High']].max(axis=1)
        series['HA_Low']=series[['HA_Open','HA_Close','Low']].min(axis=1)

        scheme["data"] = {'open':series['HA_Open'].iloc[-1],
                          'high':series['HA_High'].iloc[-1],
                          'low':series['HA_Low'].iloc[-1],
                          'close':series['HA_Close'].iloc[-1],
                          'openTime':series['date'].iloc[-1]}
        scheme["symbol"] = pair
        scheme["event"] = f"{func}_{timef}"
        scheme["open_time"] = str(int(series.iloc[-1]["date"]))

        self.schemes.append(scheme)
        LOGGER.debug("done getting heiken ashi for %s - %s", pair, scheme['open_time'])

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
        try:
            scheme["data"] = (int(supertrend2[f'SUPERTd_{timeframe}_{multiplier}.0'].iloc[-1]),
                              supertrend2[f'SUPERT_{timeframe}_{multiplier}.0'].iloc[-1])
            scheme["symbol"] = pair
            scheme["event"] = f"STX_{timeframe}"
            scheme["open_time"] = str(self.dataframes[pair].iloc[index]["openTime"])
        except TypeError:
            LOGGER.debug("overall Exception getting supertrend seq: %s", index)
            return

        self.schemes.append(scheme)
        LOGGER.debug("done getting supertrend for %s - %s", pair, scheme['open_time'])
