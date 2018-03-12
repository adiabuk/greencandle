#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
#pylint: disable=no-member,consider-iterating-dictionary,global-statement,broad-except,
#pylint: disable=unused-variable,invalid-name,logging-not-lazy,logging-format-interpolation

"""
Get ohlc (Open, High, Low, Close) values from given cryptos
and detect trends using candlestick patterns
"""

from __future__ import print_function
import json
import argparse
import time
import sys
import traceback
import calendar
import operator
from concurrent.futures import ThreadPoolExecutor
import argcomplete
import pandas
import talib
import setproctitle
import binance

from lib import balance
from lib.binance_common import get_ohlcs
from lib.support_resistance import get_values
from lib.morris import KnuthMorrisPratt
from lib.order import get_buy_price, get_sell_price
from lib.mysql import (insert_data, insert_actions, insert_action_totals, update_trades,
                       clean_stale, get_buy, get_sell, insert_trade, get_trades)

from lib.config import get_config
from lib.logger import getLogger
from indicator import SuperTrend, RSI
from profit import RATE

POOL = ThreadPoolExecutor(max_workers=50)
logger = getLogger(__name__)



class Events(dict):
    """ Represent events created from data & indicators """

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
        self.balance = balance.get_balance()
        self["hold"] = {}
        self["event"] = {}
        self.supres = {}
        if test:
            pass
            #self.data, self.dataframes = self.get_test_data(interval=interval)
        else:
            self.data, self.dataframes = data

        super(Events, self).__init__()
        logger.debug("Finished fetching raw data")

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
                print("Symbol:", value['symbol'])
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
                print("KEYERROR", value, key_error)
                continue
            print("\n")

    def get_json(self):
        """return serialized JSON of dict """
        return json.dumps(self)

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

        dataframe = self.renamed_dataframe_columns(klines)
        scheme = {}
        mine = dataframe.apply(pandas.to_numeric)
        rsi = RSI(mine)
        df_list = rsi['RSI_21'].tolist()
        df_list = ["%.1f" % float(x) for x in df_list]
        scheme["data"] = {"RSI": df_list[-1]}
        scheme["url"] = self.get_url(pair)
        scheme["time"] = calendar.timegm(time.gmtime())
        scheme["symbol"] = pair
        if float(df_list[-1]) > 70:
            direction = "overbought"
        elif float(df_list[-1]) < 30:
            direction = "oversold"
        else:
            direction = "HOLD"
        scheme["direction"] = direction
        scheme["event"] = "RSI"
        self.add_scheme(scheme)

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


        dataframe = pandas.DataFrame(klines, columns=['openTime', 'open', 'high',
                                                      'low', 'close', 'volume'])
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

        dataframe = self.renamed_dataframe_columns(klines)

        mine = dataframe.apply(pandas.to_numeric)
        supertrend = SuperTrend(mine, 10, 3)
        df_list = supertrend['STX_10_3'].tolist()
        scheme["data"] = {"SUPERTREND": df_list[-1]}
        scheme["url"] = self.get_url(pair)
        scheme["time"] = calendar.timegm(time.gmtime())
        scheme["symbol"] = pair
        scheme["direction"] = self.get_supertrend_direction(df_list[-1])
        scheme["event"] = "Supertrend"
        self.add_scheme(scheme)

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

        if 7 in [s for s in KnuthMorrisPratt(supertrend, ["down", "up", "up"])]:
            action = "BUY"
        elif 8 in [s for s in KnuthMorrisPratt(supertrend, ["up", "down"])]:
            action = "SELL"
        elif 3 in [s for s in KnuthMorrisPratt(supertrend, ["nan", "nan", "nan", "nan"])]:
            action = "UNKNOWN!"
        else:
            action = "HOLD"
        return action

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
            '<' : operator.lt,
            '>' : operator.gt,
            }[op]

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

        close = klines[-1]
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
                logger.critical("EXC")
            if result > close[-1]:
                trigger = 'SELL'
            else:
                trigger = 'BUY'

            try:
                insert_actions(pair=pair, indicator=func+'-'+str(timeperiod),
                               value=result, action=self.get_action(trigger))
            except Exception:
                traceback.print_exc()
                logger.critical("DB FUBAR")

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

        open, high, low, close = klines
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
                a = attrs['klines'][0]
                li = []
                for i in attrs['klines']:
                    li.append(locals()[i])

                j = getattr(talib, check)(*(*li, *attrs["args"]))[-1]
                #trigger = "HOLD"

                trigger = "HOLD"
                for item in "BUY", "SELL":
                    s = str(j) + " " + attrs[item]   # From numpy.float64 to str
                    if self.eval_binary_expr(*(s.split())):
                        trigger = item
                        break

            except Exception as error:
                traceback.print_exc()
                logger.critical("failed here:" + str(error))
            insert_actions(pair=pair, indicator=check, value=j, action=self.get_action(trigger))

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
        #TODO: Add data to DB

        trends = {"HAMMER": {100: "bullish", 0:"HOLD"},
                  "INVERTEDHAMMER": {100: "bearish", 0:"HOLD"},
                  "ENGULFING": {-100:"bearish", 100:"bullish", 0:"HOLD"},
                  "MORNINGSTAR": {-100:"bearish", 100:"bullish", 0:"HOLD"},
                  "SHOOTINGSTAR": {-100:"bearish", 100:"bullish", 0:"HOLD"},
                  "MARUBOZU": {-100:"bearish", 100:"bullish", 0:"HOLD"},
                  "DOJI": {100: "unknown", 0:"HOLD"}}
        results = {}
        for check in trends.keys():
            j = getattr(talib, "CDL" + check)(*klines).tolist()[-1]
            results.update({check: j})

        for check in trends.keys():
            scheme = {}
            try:
                result = trends[check][results[check][-1]]
                if "data" not in scheme:
                    scheme['data'] = {}
                scheme["data"] = results   # convert from array to list
                scheme["url"] = self.get_url(pair)
                scheme["time"] = calendar.timegm(time.gmtime())
                scheme["symbol"] = pair
                scheme["direction"] = result
                scheme["event"] = check
                scheme["difference"] = "None"
            except KeyError:
                logger.critical("KEYERROR")
                continue
        self.add_scheme(scheme)

    def add_scheme(self, scheme):
        """ add scheme to correct structure """
        pair = scheme['symbol']
        scheme.update(self.supres[pair])
        #  Add prices for current symbol to scheme
        prices = {"buy": get_buy_price(pair), "sell": get_sell_price(pair),
                  "market": binance.prices()[pair]}
        scheme.update(prices)

        bal = self.balance['binance']['TOTALS']['GBP']
        try:
            # Add scheme to DB
            insert_data(interval=self.interval, symbol=scheme['symbol'], event=scheme['event'],
                        direction=scheme['direction'], data=scheme['data'],
                        difference=str(scheme['difference']), resistance=str(scheme['resistance']),
                        support=str(scheme['support']), buy=str(scheme['buy']),
                        sell=str(scheme['sell']), market=str(scheme['market']),
                        balance=str(bal))
        except Exception as excp:

            logger.critical("Error: " + str(excp))

        if scheme["direction"] == "HOLD":
            self["hold"][id(scheme)] = scheme
        else:
            # Fetch resistance/support/PIP Value
            self["event"][id(scheme)] = scheme

            # Only creating graphs for event's that we are interested in due to the time and
            # resources that it takes
            #create_graph(self.dataframes[scheme['symbol']], scheme['symbol'])


def main():
    """ main function """
    setproctitle.setproctitle("greencandle-backend")
    parser = argparse.ArgumentParser()
    parser.add_argument('-g', '--graph', action='store_true', default=False)
    parser.add_argument('-j', '--json', action='store_true', default=False)
    parser.add_argument('-t', '--test', action='store_true', default=False)
    parser.add_argument('-p', '--pair')
    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    starttime = time.time()
    minutes = 8

    while True:
        try:
            loop(args)
        except KeyboardInterrupt:
            logger.info("\nExiting on user command...")
            sys.exit(1)
        remaining_time = (minutes * 60.0) - ((time.time() - starttime) % 60.0)
        logger.debug("Sleeping for " + str(int(remaining_time)) + " seconds")
        time.sleep(remaining_time)

def loop(args):
    """
    Loop through collection cycle
    """

    def buy(buy_list):
        """
        Buy as many items as we can from buy_list depending on max amount of trades, and current
        balance in BTC
        """
        logger.debug("We have {0} potential items to buy".format(len(buy_list)))
        if buy_list:
            current_btc_bal = events.balance['binance']['BTC']['count']
            amount_to_buy_btc = price_per_trade * RATE


            for item in buy_list:

                current_trades = get_trades()
                if amount_to_buy_btc > current_btc_bal:
                    logger.warning("Unable to purchase, insufficient funds")
                    break
                elif len(current_trades) >= max_trades:
                    logger.warning("Too many trades, skipping")
                    break
                elif item[0] in current_trades:
                    logger.warning("We already have a trade of {0}, skipping...".format(item[0]))
                    continue
                else:
                    insert_trade(item[0], prices_trunk[item[0]], price_per_trade, amount_to_buy_btc)
                    #binance.order(symbol=?, side=?, quantity, orderType='MARKET, price=?, test=True
                    #TODO: buy item
        else:
            logger.info("Nothing to buy")

    def sell(sell_list):
        """
        Sell items in sell_list
        """
        if sell_list:
            logger.info("We need to sell {0}".format(sell_list))
            for item in sell_list:
                update_trades(item, prices_trunk[item])
        else:
            logger.info("No items to sell")

    agg_data = {}
    price_per_trade = int(get_config('backend')['price_per_trade'])
    max_trades = int(get_config('backend')['max_trades'])
    logger.debug("Price per trade: {0}".format(price_per_trade))
    logger.debug("max trades: {0}".format(max_trades))

    logger.debug("Starting new cycle")
    if args.pair:
        pairs = [args.pair]
    else:
        pairs = [price for price in binance.prices().keys() if price != '123456' and
                 price.endswith("BTC")]
    prices = binance.prices()
    prices_trunk = {}
    for k, v in prices.items():
        if k.endswith("BTC"):
            prices_trunk[k] = v
    #self.data, self.dataframes = get_ohlcs(self.pairs, interval=interval)
    pairs = prices.keys()
    data = get_ohlcs(pairs, interval='15m')

    events = Events(prices=prices_trunk, data=data, interval='15m')
    data = events.get_data()
    insert_action_totals()
    clean_stale()
    sell(get_sell())
    buy(get_buy())

    try:
        if args.json:
            print(json.dumps(events, indent=4))
        else:
            events.print_text()
    except Exception:
        logger.critical("Overall exception")

    agg_data.update(data)
    return agg_data

if __name__ == '__main__':
    main()
    logger.debug("COMPLETE")
