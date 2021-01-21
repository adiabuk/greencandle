#pylint: disable=eval-used,no-else-return,unused-variable,no-member,redefined-builtin,logging-not-lazy

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

    def __init__(self, interval=None, test=False, db=0):
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
        self.host = config.redis.redis_host
        self.port = config.redis.redis_port
        self.expire = str2bool(config.redis.redis_expire)

        if test:
            test_str = "Test"
        else:
            test_str = "Live"
        self.interval = interval
        self.test = test

        self.logger.debug("Starting Redis with interval %s %s, db=%s"
                          % (interval, test_str, str(db)))
        pool = redis.ConnectionPool(host=self.host, port=self.port, db=db)
        self.conn = redis.StrictRedis(connection_pool=pool)

    def __del__(self):
        del self.conn

    def clear_all(self):
        """
        Wipe all data current redis db - used for testing only
        """
        self.conn.execute_command("flushdb")

    def add_price(self, name, data):
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
        drawup = perc_diff(orig_price, max_price)
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
        drawdown = perc_diff(orig_price, min_price)
        self.conn.delete(key)
        return drawdown if drawdown < 0 else 0

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
                self.add_price(key, data)
        elif config.main.trade_direction == 'short':
            if (min_price and float(current_high) > float(min_price)) or \
                    (not min_price and event == 'open'):
                data = {"min_price": current_low, "orig_price": orig_price}
                self.add_price(key, data)

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
                self.add_price(key, data)
        elif config.main.trade_direction == 'short':
            if (max_price and float(current_low) < float(max_price)) or \
                    (not max_price and event == 'open'):
                data = {"max_price": current_high, "orig_price": orig_price}
                self.add_price(key, data)

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

        if not key.endswith("999"):
            self.logger.critical("Invalid time submitted to redis %s.  Skipping " % key)
            return None

        for item, value in data.items():
            response = self.conn.hset(key, item, value)

        if self.expire:
            self.conn.expire(key, expiry)

        return response

    def del_key(self, key):
        """
        delete a given entry
        """
        result = self.conn.delete(key)
        self.logger.debug("Deleting key %s, result:%s" % (key, result))

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

    def get_total(self, address):
        """
        Get totals of results in each group

        Args:
              address
              eg.  b"XRPBTC:15m:1520869499999",
        Returns:
              integer value representing total score for this pair/interval/timeframe where the
              score can be negative (indicating overall bearish) - the lower the number, the more
              bearish.  Positive figures indicate bullish - the higher the number the more bullish.
              Results close to zero are considered to be HOLD (if persistent)
        """
        val = 0
        for _, value in self.conn.hgetall(address).items():
            val += ast.literal_eval(str(value.decode("UTF-8")))["action"]
        return val

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

    def get_result(self, item, indicator):
        """Retrive decoded OHLC data from redis"""
        try:
            return float(ast.literal_eval(self.get_item(item, indicator).decode())['result'])
        except (TypeError, AttributeError):
            return None

    def log_event(self, **kwargs):
        """Send event data to logger"""
        valid_keys = ["event", "rate", "perc_rate", "open_price", "close_price",
                      "pair", "current_time", "current"]
        kwargs=AttributeDict(kwargs)
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

    def get_intermittant(self, open_price, current_price):
        """
        Check if price between intervals and sell if matches stop_loss or take_profit rules
        """

        stop_loss_perc = float(config.main.stop_loss_perc)
        take_profit_perc = float(config.main.take_profit_perc)

        stop_loss_rule = float(current_price) < sub_perc(stop_loss_perc, open_price)
        take_profit_rule = float(current_price) > add_perc(take_profit_perc, open_price)

        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())

        if stop_loss_rule and open_price:
            message = "StopLoss intermittant"
            self.logger.info(message)
            return ('SELL', current_time, current_price)
        elif str2bool(config.main.take_profit) and take_profit_rule and open_price:
            message = "TakeProfit intermittant"
            self.logger.info(message)
            return ('SELL', current_time, current_price)
        else:
            return ('HOLD', current_time, current_price)

    @staticmethod
    def get_rules(rules, direction):
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
        except ValueError:

            self.logger.debug("Not enough data for %s" % pair)
            return ('HOLD', 'Not enough data', 0, {'buy':[], 'sell':[]})

        # get current & previous indicator values
        main_indicators = config.main.indicators.split()

        ind_list = []
        for i in main_indicators:

            split = i.split(';')
            ind = split[1] + '_' + split[2].split(',')[0]
            ind_list.append(ind)
        ind_list.append("SMA_vol_20")  #FIXME
        ind_list.append("volume")  #FIXME

        for indicator in ind_list:
            results['current'][indicator] = self.get_result(current, indicator)
            results['previous'][indicator] = self.get_result(previous, indicator)
            results['previous1'][indicator] = self.get_result(previous1, indicator)
            results['previous2'][indicator] = self.get_result(previous2, indicator)
            results['previous3'][indicator] = self.get_result(previous3, indicator)
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

        try:
            # function returns an empty list if no results so cannot get first element

            if str2bool(config.main.trailing_stop_loss):
                high_price = self.get_drawup(pair)['price']
                trailing_perc = float(config.main.trailing_stop_loss_perc)
                if high_price:

                    trailing_stop = current_price <= sub_perc(trailing_perc, high_price)
                    # FIXME
                    #if test_data and str2bool(config.main.immediate_stop):
                    #    trailing_stop = current_low <= sub_perc(trailing_perc, high_price)

                else:
                    trailing_stop = False
            else:
                trailing_stop = False
                high_price = open_price
            if config.main.trade_direction == "short":
                stop_loss_rule = current_price > add_perc(stop_loss_perc, open_price)
                take_profit_rule = current_price < sub_perc(take_profit_perc, open_price)

            elif config.main.trade_direction == "long":
                #FIXME - get MINPRICE
                stop_loss_rule = current_price < sub_perc(stop_loss_perc, open_price)
                take_profit_rule = current_price > add_perc(take_profit_perc, open_price)
                if test_data and str2bool(config.main.immediate_stop):
                    stop_loss_rule = current_low < sub_perc(stop_loss_perc, open_price)
                    take_profit_rule = current_high > add_perc(take_profit_perc, open_price)

        except (IndexError, ValueError, TypeError):
            # Setting to none to indicate we are currently not in a trade
            open_price = None
            stop_loss_rule = False
            take_profit_rule = False
            trailing_stop = False

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
        elif str2bool(config.main.take_profit) and take_profit_rule and open_price:
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

        self.log_event(event=event, rate=rate, perc_rate=perc_rate,
                           open_price=open_price, close_price=current_price,
                           pair=pair, current_time=current_time, current=results.current)

        winning_sell = self.get_rules(rules, 'close')
        winning_buy = self.get_rules(rules, 'open')
        self.logger.info('%s sell Rules matched: %s' % (pair, winning_sell))
        self.logger.info('%s buy Rules matched: %s' % (pair, winning_buy))
        del dbase
        return (result, current_time, current_price, {'sell':winning_sell,
                                                      'buy': winning_buy})
