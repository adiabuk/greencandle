#pylint: disable=eval-used,no-else-return,unused-variable,no-member,redefined-builtin
#pylint: disable=logging-not-lazy,inconsistent-return-statements,invalid-name

"""
Store and retrieve items from redis
"""
import ast
import time
import zlib
import pickle
from datetime import datetime
import redis
from str2bool import str2bool
from .mysql import Mysql
from .logger import get_logger
from . import config
from .common import add_perc, sub_perc, AttributeDict, perc_diff, convert_to_seconds

class Redis():
    """
    Redis object
    """

    def __init__(self, interval=None, test=False):
        """
        Args:
            interval
            host
            port
            db
        returns:
            initialized redis connection
        """
        self.logger = get_logger(__name__)
        host = config.redis.redis_host
        port = config.redis.redis_port
        db = int(config.redis.db)
        expire = str2bool(config.redis.redis_expire)

        self.interval = interval
        self.test = test

        self.logger.debug("Starting Redis with interval %s db=%s"
                          % (interval, db))
        pool = redis.ConnectionPool(host=host, port=port, db=db)
        self.conn = redis.StrictRedis(connection_pool=pool)

    def __del__(self):
        del self.conn

    def clear_all(self):
        """
        Wipe all data current redis db - used for testing only
        """
        self.conn.execute_command("flushdb")

    def __add_price(self, name, data):
        """
        add/update min and max price dict
        """
        for key, val in data.items():
            self.logger.debug("Adding to Redis: %s %s %s" % (name, key, val))
            response = self.conn.hset(name, key, val)
        return response

    def get_drawup(self, pair):
        """
        Get maximum price of current open trade for given pair/interval
        and calculate drawdup based on trade opening price.
        Return max price and drawup as a percentage
        """
        key = "{}_{}_drawup".format(pair, config.main.name)
        max_price = self.get_item(key, 'max_price')
        orig_price = self.get_item(key, 'orig_price')
        try:
            drawup = perc_diff(orig_price, max_price)
        except TypeError:
            drawup = 0
        return {'price':max_price, 'perc': drawup}

    def rm_drawup(self, pair):
        """
        Delete current draw up value for given pair
        """
        key = "{}_{}_drawup".format(pair, config.main.name)
        self.conn.delete(key)

    def rm_drawdown(self, pair):
        """
        Delete current draw down value for given pair
        """
        key = "{}_{}_drawdown".format(pair, config.main.name)
        self.conn.delete(key)

    def get_drawdown(self, pair):
        """
        Get minimum price of current open trade for given pair/interval
        and calculate drawdown based on trade opening price.
        Return min price and drawdown as a percentage
        """
        key = "{}_{}_drawdown".format(pair, config.main.name)
        min_price = self.get_item(key, 'min_price')
        orig_price = self.get_item(key, 'orig_price')
        try:
            drawdown = perc_diff(orig_price, min_price)
        except TypeError:
            drawdown = 0
        return drawdown

    def update_drawdown(self, pair, current_candle, event=None):
        """
        Update minimum price for current asset.  Create redis record if it doesn't exist.
        """
        key = "{}_{}_drawdown".format(pair, config.main.name)
        min_price = self.get_item(key, 'min_price')
        orig_price = self.get_item(key, 'orig_price')

        current_low = current_candle['low']
        current_high = current_candle['high']
        current_price = current_candle['close']

        if event == 'open':
            current_low = current_price
            current_high = current_price

        if not orig_price:
            orig_price = current_price

        if config.main.trade_direction == 'long':
            # if min price already exists and current price is lower, or there is no min price yet.

            if (min_price and float(current_low) < float(min_price)) or \
                    (not min_price and event == 'open'):

                data = {"min_price": current_low, "orig_price": orig_price}
                self.__add_price(key, data)
        elif config.main.trade_direction == 'short':
            if (min_price and float(current_high) > float(min_price)) or \
                    (not min_price and event == 'open'):
                data = {"min_price": current_low, "orig_price": orig_price}
                self.__add_price(key, data)

    def update_drawup(self, pair, current_candle, event=None):
        """
        Update minimum price for current asset.  Create redis record if it doesn't exist.
        """
        key = "{}_{}_drawup".format(pair, config.main.name)
        max_price = self.get_item(key, 'max_price')
        orig_price = self.get_item(key, 'orig_price')
        current_low = current_candle['low']
        current_high = current_candle['high']
        current_price = current_candle['close']

        if event == 'open':
            current_low = current_price
            current_high = current_price

        if not orig_price:
            orig_price = current_price
        if config.main.trade_direction == 'long':
            if (max_price and float(current_high) > float(max_price)) or \
                    (not max_price and event == 'open'):

                data = {"max_price": current_high, "orig_price": orig_price}
                self.__add_price(key, data)
        elif config.main.trade_direction == 'short':
            if (max_price and float(current_low) < float(max_price)) or \
                    (not max_price and event == 'open'):
                data = {"max_price": current_high, "orig_price": orig_price}
                self.__add_price(key, data)

    def redis_conn(self, pair, interval, data, now):
        """
        Add data to redis

        Args:
              pair: trading pair (eg. XRPBTC)
              interval: interval of each kline
              data: json with data to store
              now: datetime stamp
        Returns:
            success of operation: True/False
        """

        self.logger.debug("Adding to Redis: %s %s %s" % (interval, list(data.keys()), now))
        key = "{0}:{1}:{2}".format(pair, interval, now)
        expiry = int(config.redis.redis_expiry_seconds)

        if not key.endswith("99999") and 'event' not in data.keys(): # closing time, 1 ms before next candle
            self.logger.critical("Invalid time submitted to redis %s.  Skipping " % key)
            return None

        for item, value in data.items():
            response = self.conn.hset(key, item, value)

        if expiry:
            self.conn.expire(key, expiry)

        return response

    def get_items(self, pair, interval):
        """
        Get sorted list of keys for a trading pair/interval
        eg.
         b"XRPBTC:15m:1520869499999",
         b"XRPBTC:15m:1520870399999",
         b"XRPBTC:15m:1520871299999",
         b"XRPBTC:15m:1520872199999",
         ...

         each item in the list contains PAIR:interval:epoch (in milliseconds)
        """
        return sorted(list(self.conn.scan_iter("{0}:{1}:*".format(pair, interval))))

    def get_item(self, address, key):
        """Return a specific item from redis, given an address and key"""
        return self.conn.hget(address, key)

    def get_current(self, item):
        """
        Get the current price and date for given item where item is an address:
        eg.  b"XRPBTC:15m:1520871299999"
        All items within a group should have the same date and price, as they relate to the same
        data - so we pick an indicator at random (EMA) to reference in the JSON that is stored.
        Returns:
            a tuple of current_price and current_date
        """

        byte = self.conn.hget(item, "ohlc")
        try:
            data = ast.literal_eval(byte.decode("UTF-8"))
        except AttributeError:
            self.logger.error("No Data for item %s" % item)
            return None, None

        return data["current_price"], data["date"], data['result']

    def __get_result(self, item, indicator):
        """Retrive decoded OHLC data from redis"""
        try:
            return float(ast.literal_eval(self.get_item(item, indicator).decode())['result'])
        except (TypeError, AttributeError):
            return None

    def __log_event(self, **kwargs):
        """Send event data to logger"""
        valid_keys = ["event", "rate", "perc_rate", "open_price", "close_price",
                      "pair", "current_time", "current"]
        kwargs = AttributeDict(kwargs)
        for key in valid_keys:
            if key not in valid_keys:
                raise KeyError("Missing param %s" % key)

        message = ('EVENT:({0}) {1} rate:{2} perc_rate:{3} open_price:{4} close_price:{5}, '
                   'time:{6}'.format(kwargs.pair, kwargs.event, format(float(kwargs.rate), ".4f"),
                                     format(float(kwargs.perc_rate), ".4f"),
                                     kwargs.open_price, kwargs.close_price, kwargs.current_time))

        if kwargs.event == "Hold":
            self.logger.debug("%s, %s" % (message, kwargs.current))
        else:
            self.logger.info("%s, %s" % (message, kwargs.current))

    def get_intermittent(self, pair, open_price, current_candle):
        """
        Check if price between intervals and sell if matches stop_loss or take_profit rules
        """
        test_data = False
        stop_loss_perc = float(config.main.stop_loss_perc)
        take_profit_perc = float(config.main.take_profit_perc)
        current_price = current_candle.close
        current_high = current_candle.high
        current_low = current_candle.low

        trailing_perc = float(config.main.trailing_stop_loss_perc)
        high_price = self.get_drawup(pair)['price']
        low_price = self.get_drawdown(pair)

        stop_loss_rule = self.__get_stop_loss(test_data, current_price, current_low, open_price)

        take_profit_rule = self.__get_take_profit(test_data, current_price, current_high,
                                                  open_price)

        trailing_stop = self.__get_trailing_stop(test_data, current_price, high_price, current_high,
                                               open_price)

        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())

        if trailing_stop and open_price:
            result = "SELL"
            event  = "TrailingStop intermittent"

        elif stop_loss_rule and open_price:
            result = "SELL"
            event = "StopLoss intermittent"

        elif take_profit_rule and open_price:
            result = "SELL"
            event = "TakeProfit intermittent"

        else:
            result = "HOLD"
            event = "HOLD"

        self.__log_event(event=event, rate=0, perc_rate=0,
                       open_price=open_price, close_price=current_price,
                       pair=pair, current_time=current_time, current=0)


        return (result, event, current_time, current_price)

    @staticmethod
    def __get_trailing_stop(test_data, current_price, high_price, current_high,
                          open_price):
        """
        Check if we have reached trailing stop loss
        return True/False
        """
        trailing_perc = float(config.main.trailing_stop_loss_perc)

        if trailing_perc <= 0:
            return False

        direction = config.main.trade_direction
        immediate = str2bool(config.main.immediate_trailing_stop)
        trailing_start = float(config.main.trailing_start)
        if not high_price or not open_price:
            return False
        elif direction == 'long' and test_data and immediate:
            check = current_high
        elif direction == 'short' and test_data and immediate:
            check = current_high
        else:
            check = current_price

        if direction == "long":
            return float(check) <= sub_perc(float(trailing_perc), float(high_price)) and \
                    (test_data or float(current_price) > add_perc(float(trailing_start),
                        float(open_price)))
        elif direction == "short":
            return float(check) >= add_perc(float(trailing_perc), float(high_price))

    @staticmethod
    def __get_take_profit(test_data, current_price, current_high, open_price):
        """
        Check if we have reached take profit
        return True/False
        """
        profit_perc = float(config.main.take_profit_perc)

        if profit_perc <= 0:
            return False
        direction = config.main.trade_direction
        immediate = str2bool(config.main.immediate_take_profit)

        if not open_price:
            return False

        if direction == 'long' and test_data and immediate:
            check = current_high
        elif direction == 'short' and test_data and immediate:
            check = current_high
        else:
            check = current_price

        if direction == 'long':
            return float(check) > add_perc(float(profit_perc), float(open_price))
        elif direction == 'short':
            return float(check) < sub_perc(float(profit_perc), float(open_price))

    @staticmethod
    def __get_stop_loss(test_data, current_price, current_low, open_price):
        """
        Check if we have reached stop loss
        return True/False
        """
        direction = config.main.trade_direction
        stop_perc = float(config.main.stop_loss_perc)
        immediate = str2bool(config.main.immediate_stop)

        if not open_price:
            return False
        if direction == 'long' and test_data and immediate:
            check = current_low
        elif direction == 'short' and test_data and immediate:
            check = current_low
        else:
            check = current_price

        if direction == 'long':
            return float(check) < sub_perc(float(stop_perc), float(open_price))
        elif direction == 'short':
            return float(check) > add_perc(float(stop_perc), float(open_price))

    @staticmethod
    def __get_rules(rules, direction):
        """determine which rules have been matched"""
        winning = []
        for seq, close_rule in enumerate(rules[direction]):
            if close_rule:
                winning.append(seq + 1)
        return winning

    def get_action(self, pair, interval, test_data=False):
        """Determine if we are in a BUY/HOLD/SELL situration for a specific pair and interval"""
        results = AttributeDict(current=AttributeDict(), previous=AttributeDict(),
                                previous1=AttributeDict(), previous2=AttributeDict(),
                                previous3=AttributeDict())

        stop_loss_perc = float(config.main.stop_loss_perc)
        take_profit_perc = float(config.main.take_profit_perc)

        try:
            previous3, previous2, previous1, previous, current = \
                    self.get_items(pair=pair, interval=interval)[-5:]
        except ValueError as ve:

            self.logger.warning("Not enough data for %s: %s" % (pair, ve))
            return ('HOLD', 'Not enough data', 0, 0, {'buy':[], 'sell':[]})

        # get current & previous indicator values
        main_indicators = config.main.indicators.split()

        ind_list = []
        for i in main_indicators:
            if 'vol' in i:
                ind_list.append("volume")
            split = i.split(';')
            ind = split[1] + '_' + split[2].split(',')[0]
            ind_list.append(ind)

        for indicator in ind_list:
            results['current'][indicator] = self.__get_result(current, indicator)
            results['previous'][indicator] = self.__get_result(previous, indicator)
            results['previous1'][indicator] = self.__get_result(previous1, indicator)
            results['previous2'][indicator] = self.__get_result(previous2, indicator)
            results['previous3'][indicator] = self.__get_result(previous3, indicator)
        items = self.get_items(pair, self.interval)
        current = self.get_current(items[-1])
        previous = self.get_current(items[-2])
        current_epoch = float(current[1]) / 1000

        rehydrated = pickle.loads(zlib.decompress(current[-1]))
        last_rehydrated = pickle.loads(zlib.decompress(previous[-1]))

        # variables that can be referenced in config file
        open = float(rehydrated.open)
        high = float(rehydrated.high)
        low = float(rehydrated.low)
        close = float(rehydrated.close)
        trades = float(rehydrated.numTrades)
        last_open = float(last_rehydrated.open)
        last_high = float(last_rehydrated.high)
        last_low = float(last_rehydrated.low)
        last_close = float(last_rehydrated.close)
        last_trades = float(last_rehydrated.numTrades)
        dbase = Mysql(test=self.test, interval=interval)
        try:
            # function returns an empty list if no results so cannot get first element
            open_price, _, open_time, _, _ = dbase.get_trade_value(pair)[0]
        except IndexError:
            open_price = None
            open_time = None

        current_price = float(close)
        current_low = float(low)
        current_high = float(high)
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(current_epoch))

        # rate of Moving Average increate/decreate based on indicator
        # specified in the rate_indicator config option - best with EMA_500
        rate_indicator = config.main.rate_indicator
        perc_rate = float(perc_diff(float(results.previous[rate_indicator]),
                                    float(results.current[rate_indicator]))) \
                                    if results.previous[rate_indicator] else 0
        rate = float(float(results.current[rate_indicator]) - \
                     float(results.previous[rate_indicator])) \
                     if results.previous[rate_indicator] else 0

        last_perc_rate = float(perc_diff(float(results.previous1[rate_indicator]),
                                         float(results.previous[rate_indicator]))) \
                                               if results.previous1[rate_indicator] else 0
        last_rate = float(float(results.previous[rate_indicator]) -
                          float(results.previous1[rate_indicator])) \
                                  if results.previous1[rate_indicator] else 0

        rules = {'open': [], 'close': []}
        for seq in range(1, 10):
            current_config = None
            for rule in "open", "close":
                try:
                    current_config = config.main['{}_rule{}'.format(rule, seq)]
                    self.logger.debug("Rule: %s_rule%s: %s" % (rule, seq, current_config))
                except (KeyError, TypeError):
                    pass
                if current_config:
                    try:
                        rules[rule].append(eval(current_config))
                    except (TypeError, KeyError) as error:
                        self.logger.warning("Unable to eval config rule: %s_rule: %s %s" %
                                            (rule, current_config, error))
                        continue
        close_timeout = False
        able_to_buy = True

        if open_price:

            buy_epoch = 0 if not isinstance(open_time, datetime) else open_time.timestamp()
            sell_epoch = int(buy_epoch) + int(convert_to_seconds(config.main.time_in_trade))
            close_timeout = current_epoch > sell_epoch

        if not open_price and str2bool(config.main.wait_between_trades):
            try:
                open_time = dbase.fetch_sql_data("select close_time from trades where pair='{}' "
                                                 "and closed_by = 'api' order by close_time desc "
                                                 "LIMIT 1", header=False)[0][0]
                buy_epoch = 0 if not isinstance(open_time, datetime) else \
                    open_time.timestamp()
                pattern = '%Y-%m-%d %H:%M:%S'
                buy_epoch = open_time.timestamp()
                able_to_buy = (int(buy_epoch) +
                               int(convert_to_seconds(config.main.time_between_trades))) < \
                               current_epoch
            except (IndexError, AttributeError):
                pass  # no previous trades
        else:
            able_to_buy = True

        trailing_perc = float(config.main.trailing_stop_loss_perc)
        high_price = self.get_drawup(pair)['price']
        low_price = self.get_drawdown(pair)
        trailing_stop = self.__get_trailing_stop(test_data, current_price, high_price, current_high,
                                               open_price)
        take_profit_rule = self.__get_take_profit(test_data, current_price, current_high,
                                                  open_price)
        stop_loss_rule = self.__get_stop_loss(test_data, current_price, current_low, open_price)

        if any(rules['open']) and not able_to_buy:
            self.logger.info("Unable to buy %s due to time_between_trades" % pair)

        if open_price and any(rules['open']) and any(rules['close']):
            self.logger.warning('We ARE In a trade and have matched both buy and '
                                'sell rules for %s', pair)
            both = True
        elif not open_price and any(rules['open']) and any(rules['close']):
            self.logger.warning('We are NOT in a trade and have matched both buy and '
                                'sell rules for %s', pair)
            both = True
        else:
            both = False

        if stop_loss_rule and open_price:
            # if we match stop_loss rule and are in a trade

            if test_data and str2bool(config.main.immediate_stop):
                if config.main.trade_direction == 'short':
                    stop_at = add_perc(stop_loss_perc, open_price)
                    current_price = stop_at
                elif config.main.trade_direction == 'long':
                    stop_at = sub_perc(stop_loss_perc, open_price)
                    current_price = stop_at
            event = 'StopLoss'
            result = 'SELL'

        elif trailing_stop and open_price:

            if test_data and str2bool(config.main.immediate_stop):
                stop_at = sub_perc(trailing_perc, current_high)
                current_price = stop_at
            event = 'TrailingStopLoss'
            result = 'SELL'
        # if we match take_profit rule and are in a trade
        elif take_profit_rule and open_price:
            if test_data and str2bool(config.main.immediate_stop):
                stop_at = add_perc(take_profit_perc, open_price)
                current_price = stop_at

            event = "TakeProfit"
            result = 'SELL'

        elif close_timeout:
            event = "TimeOut"
            result = 'SELL'

        # if we match any sell rules, are in a trade and no buy rules match
        elif any(rules['close']) and open_price and not both:

            event = "NormalSell"
            result = 'SELL'

        # if we match any buy rules are NOT in a trade and sell rules don't match
        elif any(rules['open']) and not open_price and able_to_buy and not both:

            # delete and re-store high price
            self.logger.debug("Close: %s, Previous Close: %s, >: %s" %
                              (close, last_close, close > last_close))

            event = "NormalBuy"
            result = 'BUY'

        elif open_price:
            event = "Hold"
            result = 'HOLD'
        else:
            event = "NoItem"
            result = 'NOITEM'

        self.__log_event(event=event, rate=rate, perc_rate=perc_rate,
                       open_price=open_price, close_price=current_price,
                       pair=pair, current_time=current_time, current=results.current)

        winning_sell = self.__get_rules(rules, 'close')
        winning_buy = self.__get_rules(rules, 'open')
        self.logger.info('%s sell Rules matched: %s' % (pair, winning_sell))
        self.logger.info('%s buy Rules matched: %s' % (pair, winning_buy))
        del dbase
        return (result, event, current_time, current_price, {'sell':winning_sell,
                                                             'buy': winning_buy})
