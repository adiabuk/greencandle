#pylint: disable=no-member,consider-iterating-dictionary,global-statement,broad-except,
#pylint: disable=unused-variable,invalid-name,logging-not-lazy,logging-format-interpolation

from __future__ import print_function
import json
import math
import time
import sys
import traceback
import calendar
import operator
from concurrent.futures import ThreadPoolExecutor
from decimal import Decimal
import pandas
import talib
import binance
from lib.mysql import mysql
from lib.redis_conn import Redis
from lib import balance
from lib.support_resistance import get_values
from lib.order import get_buy_price, get_sell_price

from lib.logger import getLogger, get_decorator
from indicator import SuperTrend, RSI


POOL = ThreadPoolExecutor(max_workers=50)
logger = getLogger(__name__)

class Engine(dict):
    """ Represent events created from data & indicators """

    get_exceptions = get_decorator((Exception), default_value="default")
    def __init__(self, data, prices, interval=None, test=False):
        """
        Initialize class
        Create hold and event dicts
        Fetch initial data from binance and store within object
        """
        logger.debug("Fetching raw data")
        self.interval = interval
        self.pairs = prices.keys()
        self.dataframe = None
        self.redis = Redis()
        self.db = mysql()
        if not test:
            self.balance = balance.get_balance()
        self.test = test
        self["hold"] = {}
        self["event"] = {}
        self.supres = {}
        self.data, self.dataframes = data
        super(Engine, self).__init__()
        logger.debug("Finished fetching raw data")

    def __del__(self):
        del  self.db
        del self.redis

    def get_test_data(self, data):
        """Get test data"""
        pass

    def print_text(self):
        """
        Print text output to stdout
        """

        red = "\033[31m"
        white = "\033[0m"
        if not self.values:
            logger.critical("ERROR")
        for value in self.values():
            if not "direction" in value or "HOLD" in value["direction"]:
                #no_change.append(value["symbol"])
                continue
            try:
                print("Symbol:", value["symbol"])
                print("URL:", value["url"])
                if value["direction"] != "HOLD":
                    print("direction:", red, value["direction"], white)
                else:
                    print("direction:", value["direction"])
                print("event:", red, value["event"], white)
                print("time:", value["time"])
                for key2, value2 in value["data"].items():
                    print(key2, value2)
            except KeyError as key_error:
                print("AMROX25 KEYERROR", value, key_error)
                continue
            print("\n")

    def get_json(self):
        """return serialized JSON of dict """
        return json.dumps(self)

    @get_exceptions
    def get_data(self):
        """
        Iterate through data and trading pairs to extract data
        Run data through indicator, oscillators, moving average
        Return dict containing alert data and hold data

        Args: None

        Returns:
            dict containing all collected data
        """
        logger.debug("Getting data")
        global POOL
        POOL = ThreadPoolExecutor(max_workers=400)
        for pair in self.pairs:

            # get indicators supertrend, and API for each trading pair
            POOL.submit(self.get_sup_res, pair, self.dataframes[pair])
            POOL.submit(self.get_indicators, pair, self.data[pair])
            POOL.submit(self.get_oscillators, pair, self.data[pair])
            POOL.submit(self.get_moving_averages, pair, self.data[pair])
            POOL.submit(self.get_supertrend, pair, self.dataframes[pair])
            POOL.submit(self.get_rsi, pair, self.dataframes[pair])

        POOL.shutdown(wait=True)
        POOL = ThreadPoolExecutor(max_workers=50)
        logger.debug("Done getting data")
        return self

    def get_sup_res(self, pair, klines):
        """
        get support & resistance values for current pair
        Append data to supres instance variable (dict)

        Args:
              pair: trading pair (eg. XRPBTC)
              klines: pandas dataframe containing data for specified pair
        Returns:
            None
        """

        values = get_values(pair, klines)
        self.supres[pair] = values

    def get_rsi(self, pair=None, klines=None):
        """
        get RSI oscillator values for given pair
        Append current RSI data to instance variable

        Args:
              pair: trading pair (eg. XRPBTC)
              klines: pandas dataframe containing data for specified pair
        Returns:
            None

        """
        logger.info("Getting RSI")
        dataframe = self.renamed_dataframe_columns(klines)
        scheme = {}
        mine = dataframe.apply(pandas.to_numeric)
        rsi = RSI(mine)
        df_list = rsi["RSI_21"].tolist()
        df_list = ["%.1f" % float(x) for x in df_list]
        scheme["data"] = df_list[-1]
        scheme["url"] = self.get_url(pair)
        scheme["time"] = calendar.timegm(time.gmtime())
        scheme["symbol"] = pair
        if float(df_list[-1]) > 70:
            direction = "SELL"
        elif float(df_list[-1]) < 30:
            direction = "BUY"
        else:
            direction = "HOLD"
        scheme["direction"] = direction
        scheme["event"] = "RSI"
        self.add_scheme(scheme)
        logger.info("Done getting RSI")

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

    def get_supertrend(self, pair=None, klines=None):
        """
        Get the super trend oscillator values for a given pair
        append current supertrend data to instance variable

        Args:
              pair: trading pair (eg. XRPBTC)
              klines: pandas dataframe containing data for specified pair
        Returns:
            None

        """

        scheme = {}
        logger.info("getting supertrend")
        dataframe = self.renamed_dataframe_columns(klines)

        mine = dataframe.apply(pandas.to_numeric)
        supertrend = SuperTrend(mine, 10, 3)
        df_list = supertrend["STX_10_3"].tolist()
        scheme["data"] = df_list[-1]
        scheme["url"] = self.get_url(pair)
        scheme["time"] = calendar.timegm(time.gmtime())
        scheme["symbol"] = pair
        scheme["direction"] = self.get_supertrend_direction(df_list[-1])
        scheme["event"] = "Supertrend"
        self.add_scheme(scheme)
        logger.info("done getting supertrend")

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
            result = "BUY"
        elif supertrend == "down":
            result = "SELL"
        else:
            result = "HOLD"
        return result

    @staticmethod
    def get_operator_fn(op):
        """
        Get operator function from string
        Args:
            op: string operator "<" or ">"
        Returns:
            operator.lt or operator.gt function
        """

        return {
            "<" : operator.lt,
            ">" : operator.gt,
            }[op]

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

    @staticmethod
    def get_action(trigger):
        """
        Transform action into an integer so that overall sentiment for a pair can be easily
        calculated

        Args:
            trigger: BUY/SELL/HOLD

        Returns:
            integer representation of given trigger.  BUY=1, SELL=-1, HOLD=0

        """


        return {"BUY": 1,
                "SELL": -1,
                "HOLD": 0}[trigger]

    @get_exceptions
    def get_moving_averages(self, pair, klines):
        """
        Apply moving averages to klines and get BUY/SELL triggers
        Add data to DB

        Args:
            pair: trading pair (eg. XRPBTC)
            klines: tuple of ohlc float values

        Returns:
            None
        """
        logger.debug("getting moving averages")
        try:
            close = klines[-1]
        except Exception as e:
            logger.critical("AMROX25 FAILING!!! " + str(e))
        trends = (
            ("EMA", 10),
            ("EMA", 20),
            ("EMA", 30),
            ("EMA", 50),
            ("EMA", 100),
            ("SMA", 200),
            ("SMA", 20),
            ("SMA", 30),
            ("SMA", 50),
            ("SMA", 100),
            ("SMA", 200))
        for func, timeperiod in trends:
            try:
                result = getattr(talib, func)(close, timeperiod)[-1]
            except Exception:
                logger.critical("AMROX25 EXC")
            if result > close[-1]:
                trigger = "SELL"
            else:
                trigger = "BUY"
            scheme = {}
            result = 0.0 if math.isnan(result) else result
            try:
                current_price = str(Decimal(self.dataframes[pair].iloc[-1]["close"]))
                close_time = str(self.dataframes[pair].iloc[-1]["closeTime"])
                data = {func+"-"+str(timeperiod):{"result": result,
                                                  "current_price":current_price,
                                                  "date":close_time,
                                                  "action":self.get_action(trigger)}}
                scheme["data"] = result
                scheme["url"] = "google.com"
                scheme["time"] = calendar.timegm(time.gmtime())
                scheme["symbol"] = pair
                scheme["direction"] = trigger
                scheme["event"] = func+"-"+str(timeperiod)
                scheme["difference"] = None

                self.add_scheme(scheme)

            except KeyError as e:
                logger.critical("AMROX25 KEY FAILURE " + str(e))

        logger.debug("done getting moving averages")

    @get_exceptions
    def get_oscillators(self, pair, klines):
        """

        Apply osscilators to klines and get BUY/SELL triggers
        Add data to DB

        Args:
            pair: trading pair (eg. XRPBTC)
            klines: tuple of ohlc float values

        Returns:
            None
        """
        logger.info("Getting Oscillators")
        open, high, low, close = klines
        scheme = {}
        trends = {
            #"STOCHF": {"BUY": "< 25", "SELL": ">75", "args":[20]},
            "CCI": {"BUY": "< -100", "SELL": "> 100",
                    "klines": ("high", "low", "close"), "args": [14]},
            #"ADX": {"BUY": ???
            "RSI": {"BUY": "< 30", "SELL": "> 70", "klines": tuple(("close",)), "args": [14]},
            "MOM": {"BUY": "< 0", "SELL": "> 0", "klines": tuple(("close",)), "args": [10]},
            "APO": {"BUY": "> 0", "SELL": "< 0", "klines": tuple(("close",)), "args": []},
            "ULTOSC": {"BUY": "< 30", "SELL": "> 70",
                       "klines": ("high", "low", "close"), "args":[7, 14, 28]},
            "WILLR": {"BUY": "> 80", "SELL": "< 20",
                      "klines": ("high", "low", "close"), "args": [14]},
            "AROONOSC": {"BUY": "> 50", "SELL": "< -50", "klines": ("high", "low"), "args": []}
            }

        for check, attrs in trends.items():
            try:
                a = attrs["klines"][0]
                li = []
                for i in attrs["klines"]:
                    li.append(locals()[i])

                j = getattr(talib, check)(*(*li, *attrs["args"]))[-1]
                trigger = "HOLD"
                for item in "BUY", "SELL":
                    s = str(j) + " " + attrs[item]   # From numpy.float64 to str
                    if self.eval_binary_expr(*(s.split())):
                        trigger = item
                        self.db.insert_actions(pair=pair, indicator=check, value=j,
                                               action=self.get_action(trigger))
                        break

            except Exception as error:
                traceback.print_exc()
                logger.critical("AMROX 25 failed here:" + str(error))

            current_price = str(Decimal(self.dataframes[pair].iloc[-1]["close"]))
            close_time = str(self.dataframes[pair].iloc[-1]["closeTime"])
            result = 0.0 if math.isnan(j) else j
            try:
                data = {check:{"result": result,
                               "date": close_time,
                               "current_price":current_price,
                               "action":self.get_action(trigger)}}
                scheme["data"] = result
                scheme["url"] = "google.com"
                scheme["time"] = calendar.timegm(time.gmtime())
                scheme["symbol"] = pair
                scheme["direction"] = trigger
                scheme["event"] = check
                scheme["difference"] = None

                self.add_scheme(scheme)

            except KeyError as e:
                logger.critical("AMROX25 Key failure " + str(e))
        logger.info("Done getting Oscillators")

    @get_exceptions
    def get_indicators(self, pair, klines):
        """

        Cross Reference data against trend indicators
        Apply osscilators to klines and get BUY/SELL triggers

        Args:
            pair: trading pair (eg. XRPBTC)
            klines: tuple of ohlc float values

        Returns:
            None
        """
        logger.info("Getting Indicators")
        trends = {"HAMMER": {100: "BUY", 0:"HOLD"},
                  "INVERTEDHAMMER": {100: "SELL", 0:"HOLD"},
                  "ENGULFING": {-100:"SELL", 100:"BUY", 0:"HOLD"},
                  "MORNINGSTAR": {-100:"SELL", 100:"BUY", 0:"HOLD"},
                  "SHOOTINGSTAR": {-100:"SELL", 100:"BUY", 0:"HOLD"},
                  "MARUBOZU": {-100:"SELL", 100:"BUY", 0:"HOLD"},
                  "DOJI": {100: "HOLD", 0:"HOLD"}}

        for check in trends.keys():
            scheme = {}
            try:

                result = getattr(talib, "CDL" + check)(*klines).tolist()[-1]
                scheme["data"] = result   # convert from array to list
                scheme["url"] = self.get_url(pair)
                scheme["time"] = calendar.timegm(time.gmtime())
                scheme["symbol"] = pair
                scheme["direction"] = trends[check][result]
                scheme["event"] = check
                scheme["difference"] = "None"

                self.add_scheme(scheme)
            except KeyError as ke:
                logger.critical("AMROX25 KEYERROR "  + str(sys.exc_info()))
                continue

        logger.info("Done getting Indicators")

    @get_exceptions
    def add_scheme(self, scheme):
        """ add scheme to correct structure """
        pair = scheme["symbol"]
        #scheme.update(self.supres[pair])  #FIXME

        # add to redis
        current_price = str(Decimal(self.dataframes[pair].iloc[-1]["close"]))
        close_time = str(self.dataframes[pair].iloc[-1]["closeTime"])
        result = 0.0 if (isinstance(scheme["data"], float) and
                         math.isnan(scheme["data"]))  else scheme["data"]
        try:
            data = {scheme["event"]:{"result": str(result),
                                     "current_price": float(current_price),
                                     "date": close_time,
                                     "action":self.get_action(scheme["direction"])}}

            self.redis.redis_conn(pair, self.interval, data, close_time)

        except Exception as e:
            logger.critical("AMROX25 Redis failure22 " +str(e) + " " + repr(sys.exc_info()))


        if not self.test:
            #  Add prices for current symbol to scheme
            prices = {"buy": get_buy_price(pair), "sell": get_sell_price(pair),
                      "market": binance.prices()[pair]}
            scheme.update(prices)

            bal = self.balance["binance"]["TOTALS"]["GBP"]

            # Add scheme to DB
            try:
                self.db.insert_data(interval=self.interval,
                                    symbol=scheme["symbol"], event=scheme["event"],
                                    direction=scheme["direction"], data=scheme["data"],
                                    difference=str(scheme["difference"]),
                                    resistance=str(scheme["resistance"]),
                                    support=str(scheme["support"]), buy=str(scheme["buy"]),
                                    sell=str(scheme["sell"]), market=str(scheme["market"]),
                                    balance=str(bal))
            except Exception as excp:
                logger.critical("AMROX25 Error: " + str(excp))

        if scheme["direction"] == "HOLD":
            self["hold"][id(scheme)] = scheme
        else:
            # Fetch resistance/support/PIP Value
            self["event"][id(scheme)] = scheme
