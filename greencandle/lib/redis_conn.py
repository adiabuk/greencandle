#pylint: disable=eval-used,no-else-return,unused-variable,no-member,redefined-builtin,broad-except
#pylint: disable=logging-not-lazy,inconsistent-return-statements,invalid-name

"""
Store and retrieve items from redis
"""
import json
import time
import zlib
import pickle
from datetime import datetime, timedelta
import redis
from str2bool import str2bool
from greencandle.lib.mysql import Mysql
from greencandle.lib.logger import get_logger
from greencandle.lib import config
from greencandle.lib.common import add_perc, sub_perc, AttributeDict, \
        perc_diff, convert_to_seconds, TF2MIN

class Redis():
    """
    Redis object
    """

    def __init__(self, interval=config.main.interval, test_data=False, db=0):
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
        expire = str2bool(config.redis.redis_expire)

        self.interval = interval
        self.test_data = test_data

        self.logger.debug("Starting Redis with interval %s db=%s"
                          % (self.interval, db))
        pool = redis.ConnectionPool(host=host, port=port, db=db)
        self.conn = redis.StrictRedis(connection_pool=pool)

    def __del__(self):
        """destroy instance"""
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
        redis1 = Redis(db=2)
        for key, val in data.items():
            self.logger.debug("Adding to Redis: %s %s %s" % (name, key, val))
            response = redis1.conn.hset(name, key, val)
        del redis1
        return response

    def get_drawup(self, pair):
        """
        Get maximum price of current open trade for given pair/interval
        and calculate drawdup based on trade opening price.
        Return max price and drawup as a percentage
        """
        redis1 = Redis(db=2)
        key = "{}_{}_drawup".format(pair, config.main.name)
        max_price = redis1.get_item(key, 'max_price')
        orig_price = redis1.get_item(key, 'orig_price')
        try:
            drawup = perc_diff(orig_price, max_price)
        except TypeError:
            drawup = 0
        self.logger.debug("Getting %s drawup orig_price: %s,  max_price: %s, drawup: %s"
                          % (pair, orig_price, max_price, drawup))
        del redis1
        return {'price':max_price, 'perc': drawup}

    def rm_drawup(self, pair):
        """
        Delete current draw up value for given pair
        """
        redis1 = Redis(db=2)
        key = "{}_{}_drawup".format(pair, config.main.name)
        redis1.conn.delete(key)
        del redis1

    def rm_drawdown(self, pair):
        """
        Delete current draw down value for given pair
        """
        redis1 = Redis(db=2)
        key = "{}_{}_drawdown".format(pair, config.main.name)
        redis1.conn.delete(key)
        del redis1

    def get_drawdown(self, pair):
        """
        Get minimum price of current open trade for given pair/interval
        and calculate drawdown based on trade opening price.
        Return min price and drawdown as a percentage
        """
        redis1 = Redis(db=2)
        key = "{}_{}_drawdown".format(pair, config.main.name)
        min_price = redis1.get_item(key, 'min_price')
        orig_price = redis1.get_item(key, 'orig_price')
        try:
            drawdown = perc_diff(orig_price, min_price)
        except TypeError:
            drawdown = 0
        self.logger.debug("Getting %s drawdown orig_price: %s,  min_price: %s, drawdown: %s"
                          % (pair, orig_price, min_price, drawdown))
        del redis1
        return drawdown

    def update_on_entry(self, pair, name, value):
        """
        Update key/value for storing profit/stoploss from figures derived at trade entry
        """
        redis1 = Redis(db=2)
        key = "{}-{}-{}".format(pair, name, config.main.name)
        redis1.conn.set(key, value)
        del redis1

    def get_on_entry(self, pair, name):
        """
        fetch key/value set on trade entry
        If no value exists, retrieve default from config
        Returns float
        """
        redis1 = Redis(db=2)
        key = "{}-{}-{}".format(pair, name, config.main.name)
        value = redis1.conn.get(key)

        try:
            result = float(value.decode())
        except AttributeError:
            result = float(config.main[name])
        del redis1
        return result

    def rm_on_entry(self, pair, name):
        """
        Remove key/value pair set at trade entry
        This is normally done on trade exit
        """
        redis1 = Redis(db=2)
        key = "{}-{}-{}".format(pair, name, config.main.name)
        return redis1.conn.delete(key)

    @staticmethod
    def in_current_candle(open_time):
        """
        Check we are still within the current candle
        If open_time + min(interval) is in the future
        """
        if not open_time:
            return False
        else:
            current_time = datetime.now()
            future_time = open_time + timedelta(minutes=TF2MIN[config.main.interval])
        return bool(future_time > current_time)

    def update_drawdown(self, pair, current_candle, event=None, open_time=None):
        """
        Update minimum price for current asset.  Create redis record if it doesn't exist.
        """
        redis1 = Redis(db=2)
        key = "{}_{}_drawdown".format(pair, config.main.name)
        min_price = redis1.get_item(key, 'min_price')
        orig_price = redis1.get_item(key, 'orig_price')

        current_low = current_candle['low']
        current_high = current_candle['high']
        current_price = current_candle['close']

        if event == 'open':
            self.rm_drawdown(pair)
            current_low = current_price
            current_high = current_price

        self.logger.debug("Calling update_drawdown %s" % current_candle['close'])
        if not orig_price:
            orig_price = current_price

        if config.main.trade_direction == 'long':
            # if min price already exists and current price is lower, or there is no min price yet.
            price = current_price if self.in_current_candle(open_time) else current_low
            self.logger.debug("We are long")

            if (min_price and float(price) < float(min_price)) or \
                    (not min_price and event == 'open'):

                data = {"min_price": price, "orig_price": orig_price}
                self.logger.debug("Setting long data")
                self.__add_price(key, data)
        elif config.main.trade_direction == 'short':
            price = current_price if self.in_current_candle(open_time) else current_high
            if (min_price and float(price) > float(min_price)) or \
                    (not min_price and event == 'open'):
                data = {"min_price": price, "orig_price": orig_price}
                self.logger.debug("Setting short data")
                self.__add_price(key, data)

    def update_drawup(self, pair, current_candle, event=None, open_time=None):
        """
        Update minimum price for current asset.  Create redis record if it doesn't exist.
        """
        redis1 = Redis(db=2)
        key = "{}_{}_drawup".format(pair, config.main.name)
        max_price = redis1.get_item(key, 'max_price')
        orig_price = redis1.get_item(key, 'orig_price')
        current_low = current_candle['low']
        current_high = current_candle['high']
        current_price = current_candle['close']

        if event == 'open':
            self.rm_drawup(pair)
            current_low = current_price
            current_high = current_price
        self.logger.debug("Calling update_drawup %s" % current_candle['close'])
        if not orig_price:
            orig_price = current_price
        if config.main.trade_direction == 'long':
            price = current_price if self.in_current_candle(open_time) else current_high
            if (max_price and float(price) > float(max_price)) or \
                    (not max_price and event == 'open'):

                data = {"max_price": price, "orig_price": orig_price}
                self.__add_price(key, data)
        elif config.main.trade_direction == 'short':
            price = current_price if self.in_current_candle(open_time) else current_low
            if (max_price and float(price) < float(max_price)) or \
                    (not max_price and event == 'open'):
                data = {"max_price": price, "orig_price": orig_price}
                self.__add_price(key, data)

    def append_data(self, pair, interval, data):
        """
        Add data to existing redis keys
        """
        date = data['event']['date']
        key = "{0}:{1}".format(pair, interval)
        byte = self.conn.hmget(key, date)
        if byte[0]:
            decoded = json.loads(byte[0].decode())
            decoded.update(data)
            recoded = json.dumps(decoded)
            result = self.conn.hmset(key, {date: recoded})
        else:
            result = self.conn.hmset(key, {date: json.dumps(data)})
        return result

    def add_data(self, pair, interval, data):
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

        #self.logger.debug("Adding to Redis: %s %s %s" % (pair, list(data.keys()), now))
        for close, value in data.items():
            key = "{0}:{1}".format(pair, interval)
            expiry = int(config.redis.redis_expiry_seconds)
            # closing time, 1 ms before next candle
            if not str(close).endswith("999"): # closing time, 1 ms before next candle
                self.logger.critical("Invalid time submitted to redis %s.  Skipping " % key)
                continue
            result = self.conn.hmset(key, {close: json.dumps(value)})

        if str2bool(config.redis.redis_expire):
            self.conn.expire(key, expiry)

        return True

    def get_items(self, pair, interval):
        """
        Get sorted list of available keys for a given trading pair/interval
        eg.
         "1520869499999",
         "1520870399999",
         "1520871299999",
         "1520872199999",
         ...

         each item in the list is a key to the hash containing data for that given period
        """
        key = "{}:{}".format(pair, interval)
        return sorted([item.decode() for item in list(self.conn.hgetall(key).keys())])

    def get_item(self, address, key, pair=None, interval=None):
        """Return a specific item from redis, given an address and key"""
        if pair:
            try:
                item = json.loads(self.conn.hget("{}:{}".format(pair, interval),
                                                 address).decode())[key]
                return item
            except KeyError as ke:
                self.logger.warning("Unable to get key for %s: %s %s" % (address, key, str(ke)))
                return None
        item = self.conn.hget(address, key)
        return item

    def hgetall(self):
        """
        Log current redis hashes for debugging unit tests
        """
        for key in self.conn.keys():
            self.logger.critical("%s %s" % (key, self.conn.hgetall(key)))

    def get_current(self, name, item):
        """
        Get the current price and data for given item where name is an address:
        eg.  "XRPBTC:15m"
        and item is an mepoch eg. "1520871299999"
        All items within a group should have the same date and price, as they relate to the same
        data - so we pick an indicator at random (EMA) to reference in the JSON that is stored.
        Returns:
            a tuple of current_price and current_date
        """
        byte = self.conn.hget(name, item)

        try:
            data = json.loads(byte.decode("UTF-8"))['ohlc']
            current_price = data['close']
        except KeyError:
            self.logger.error("No Data for item %s %s" % (name, item))
            return None, None, None
        return current_price, item, data

    def get_result(self, item, indicator, pair=None, interval=None):
        """
        Retrive result of a particular indicator for given item (mepoch)
        args:
          item: mepoch
          indicator: eg. EMA_200
          pair
          interval
        """
        try:
            self.logger.debug("Running get_result %s %s %s %s" %(item, indicator, pair, interval))
            result = self.get_item(item, indicator, pair, interval)
        except AttributeError:
            return None

        try:
            return float(result)
        except TypeError:
            return result

    def __log_event(self, pair, event, current_time, data):
        """Send event data to logger"""

        message = ('EVENT:({0}) {1} time:{2} data:{3}'.format(pair, event, current_time, data))

        if any(status in event for status in ['NOITEM', 'HOLD']):
            self.logger.debug(message)
        else:
            self.logger.info(message)

    def get_intermittent(self, pair, open_price, current_candle, open_time):
        """
        Check if price between intervals and sell if matches stop_loss or take_profit rules
        """
        stop_loss_perc = self.get_on_entry(pair, 'stop_loss_perc')
        take_profit_perc = self.get_on_entry(pair, 'take_profit_perc')

        current_price = current_candle.close
        current_high = current_candle.high
        current_low = current_candle.low

        trailing_perc = float(config.main.trailing_stop_loss_perc)
        high_price = self.get_drawup(pair)['price']
        low_price = self.get_drawdown(pair)

        stop_loss_rule = self.__get_stop_loss(current_price, current_low, open_price, pair)

        take_profit_rule = self.__get_take_profit(current_price, current_high, open_price, pair)

        trailing_stop = self.__get_trailing_stop(current_price, high_price, low_price, current_high,
                                                 current_low, open_price)

        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())

        open_epoch = 0 if not isinstance(open_time, datetime) else open_time.timestamp()
        sell_epoch = int(open_epoch) + int(convert_to_seconds(config.main.time_in_trade))
        current_epoch = int(time.time())

        if open_price:
            close_timeout = current_epoch > sell_epoch
            close_timeout_price = self.__get_timeout_profit(open_price, current_price)

            if trailing_stop:
                result = "CLOSE"
                event = self.get_event_str("TrailingStopIntermittent" + result)

            elif close_timeout and close_timeout_price:
                result = 'CLOSE'
                event = self.get_event_str("TimeOut" + result)

            elif stop_loss_rule:
                result = "CLOSE"
                event = self.get_event_str("StopIntermittent" + result)

            elif take_profit_rule:
                result = "CLOSE"
                event = self.get_event_str("TakeProfitIntermittent" + result)

            else:
                result = "HOLD"
                event = self.get_event_str(result)
        else:
            result = "NOITEM"
            event = self.get_event_str(result)

        self.__log_event(pair=pair, event=event, current_time=current_time, data=0)

        return (result, event, current_time, current_price)

    def __get_trailing_stop(self, current_price, high_price, low_price, current_high, current_low,
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
        elif direction == 'long' and self.test_data and immediate:
            check = current_high
        elif direction == 'short' and self.test_data and immediate:
            check = current_low
        else:
            check = current_price

        if direction == "long":
            result = float(check) <= sub_perc(float(trailing_perc), float(high_price)) and \
                    (self.test_data or float(current_price) > add_perc(float(trailing_start),
                                                                       float(open_price)))
        elif direction == "short":
            result = float(check) >= sub_perc(float(trailing_perc), float(low_price)) and \
                    (self.test_data or float(current_price) < sub_perc(float(trailing_start),
                                                                       float(open_price)))

        if result:
            high_price = low_price if direction == "short" else high_price
            self.logger.info("TrailingStopLoss reached high_price: %s current_price: %s "
                             "open_price: %s" % (high_price, current_price, open_price))
        return result

    @staticmethod
    def __get_timeout_profit(open_price, current_price):
        """
        Check if we have reached timeout perc
        """

        perc = float(config.main.perc_at_timeout)
        direction = config.main.trade_direction

        if direction == 'long':
            result = float(current_price) > add_perc(float(perc), float(open_price))
        elif direction == 'short':
            result = float(current_price) < sub_perc(float(perc), float(open_price))
        return result

    def __get_take_profit(self, current_price, current_high, open_price, pair):
        """
        Check if we have reached take profit
        return True/False
        """

        profit_perc = self.get_on_entry(pair, 'take_profit_perc')
        if profit_perc <= 0:
            return False
        direction = config.main.trade_direction
        immediate = str2bool(config.main.immediate_take_profit)

        if not open_price:
            return False

        if direction == 'long' and self.test_data and immediate:
            check = current_high
        elif direction == 'short' and self.test_data and immediate:
            check = current_high
        else:
            check = current_price

        if direction == 'long':
            result = float(check) > add_perc(float(profit_perc), float(open_price))
        elif direction == 'short':
            result = float(check) < sub_perc(float(profit_perc), float(open_price))

        if result:
            self.logger.info("TakeProfit reached current_high: %s current_price: %s "
                             "open_price: %s" % (current_high, current_price, open_price))
        return result

    def __get_stop_loss(self, current_price, current_low, open_price, pair):
        """
        Check if we have reached stop loss
        return True/False
        """
        direction = config.main.trade_direction

        stop_perc = self.get_on_entry(pair, 'stop_loss_perc')
        immediate = str2bool(config.main.immediate_stop)

        if not open_price:
            return False
        if direction == 'long' and self.test_data and immediate:
            check = current_low
        elif direction == 'short' and self.test_data and immediate:
            check = current_low
        else:
            check = current_price

        if direction == 'long':
            result = float(check) < sub_perc(float(stop_perc), float(open_price))
        elif direction == 'short':
            result = float(check) > add_perc(float(stop_perc), float(open_price))

        if result:
            self.logger.info("StopLoss reached current_low: %s current_price: %s "
                             "open_price: %s" % (current_low, current_price, open_price))
        return result

    @staticmethod
    def __get_rules(rules, direction):
        """determine which rules have been matched"""
        winning = []
        for seq, close_rule in enumerate(rules[direction]):
            if close_rule:
                winning.append(seq + 1)
        return winning

    @staticmethod
    def get_event_str(action):
        """
        Return trade string for use in logs & notifications
        """
        trade_direction = config.main.trade_direction
        trade_type = config.main.trade_type
        return "{}_{}_{}".format(trade_direction, trade_type, action)

    def get_last_candle(self, pair, interval):
        """
        Get final reconstructed candle data
        """
        last_item = self.get_items(pair, interval)[-1]
        raw = self.get_current('{}:{}'.format(pair, interval), last_item)
        try:
            return raw[-1]
        except Exception:  # hack for unit tests still using pickled zlib objects
            return pickle.loads(zlib.decompress(raw[-1]))

    def get_action(self, pair, interval):
        """
        Determine if we are in a OPEN/HOLD/CLOSE/NOITEM state for a specific pair and interval
        Will retrieve the current and previous 4 elements from redis and run open/close rules, as
        well as assessing stop_loss and take_profit status
        Retruns: tupple of dicts containing data
        eg
          ('NOITEM',                 -- status
           'long_spot_NOITEM',       -- status name
           '2022-09-30 16:09:59',    -- current date/time stamp
           0.068467,                 -- current price of asset
           {'close': [], 'open': []})  -- matched open/close rules
        """
        main_indicators = config.main.indicators.split()

        ind_list = []
        for i in main_indicators:
            if 'vol' in i:
                ind_list.append("volume")
            split = i.split(';')
            ind = split[1] + '_' + split[2].split(',')[0]
            ind_list.append(ind)

        res = []
        name = "{}:{}".format(pair, self.interval)
        # loop backwards through last 5 items
        try:
            items = self.get_items(pair=pair, interval=interval)
            _ = items[-5]
        except (ValueError, IndexError) as err:
            self.logger.warning("Not enough data for %s: %s" % (pair, err))
            return ('HOLD', 'Not enough data', 0, 0, {'open':[], 'close':[]})

        for i in range(-1, -6, -1):
            x = AttributeDict()
            for indicator in ind_list:
                x[indicator] = self.get_result(items[i], indicator, pair, self.interval)

            # Floatify each of the ohlc elements before adding
            ohlc = self.get_current(name, items[i])[-1]
            for item in ['open', 'high', 'low', 'close']:
                ohlc[item] = float(ohlc[item])

            x.update(ohlc)
            res.append(x)

        stop_loss_perc = self.get_on_entry(pair, 'stop_loss_perc')
        take_profit_perc = self.get_on_entry(pair, 'take_profit_perc')

        if stop_loss_perc:
            stop_loss_perc = float(stop_loss_perc)
        else:
            stop_loss_perc = 0

        if take_profit_perc:
            take_profit_perc = float(take_profit_perc)
        else:
            take_profit_perc = 0

        current_epoch = float(items[-1]) / 1000

        dbase = Mysql(test=self.test_data, interval=interval)

        try:
            # function returns an empty list if no results so cannot get first element
            open_price, _, open_time, _, _, _ = dbase.get_trade_value(pair)[0]
        except IndexError:
            open_price = None
            open_time = None

        current_price = float(res[0].close)
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(current_epoch))

        # rate of Moving Average increate/decreate based on indicator
        # specified in the rate_indicator config option - best with EMA_500
        rate_indicator = config.main.rate_indicator

        for i in range(0, 4):
            # loop through first 4 results (can't use 5th as we will need
            # following item which doesn't exist
            res[i]['perc_rate'] = float(perc_diff(float(res[i+1][rate_indicator]),
                                                  float(res[i][rate_indicator]))) \
                                        if res[i][rate_indicator] and \
                                        res[i+1][rate_indicator] else 0
            res[i]['rate'] = float(float(res[i][rate_indicator]) - \
                                   float(res[i+1][rate_indicator])) \
                                   if res[i][rate_indicator] and \
                                   res[i+1][rate_indicator] else 0

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
                        self.logger.warning("Unable to eval config rule for pair %s: %s_rule: %s"
                                            "%s mepoch: %s" % (pair, rule, current_config, error,
                                                               items[seq]))
                        continue
        close_timeout = False
        able_to_open = True

        if open_price:

            open_epoch = 0 if not isinstance(open_time, datetime) else open_time.timestamp()
            sell_epoch = int(open_epoch) + int(convert_to_seconds(config.main.time_in_trade))
            close_timeout = current_epoch > sell_epoch
            close_timeout_price = self.__get_timeout_profit(open_price, current_price)

        if not open_price and str2bool(config.main.wait_between_trades):
            try:
                open_time = dbase.fetch_sql_data("select close_time from trades where pair='{}' "
                                                 "and closed_by = 'api' order by close_time desc "
                                                 "LIMIT 1", header=False)[0][0]
                open_epoch = 0 if not isinstance(open_time, datetime) else \
                    open_time.timestamp()
                pattern = '%Y-%m-%d %H:%M:%S'
                able_to_open = (int(open_epoch) +
                                int(convert_to_seconds(config.main.time_between_trades))) < \
                                current_epoch
            except (IndexError, AttributeError):
                pass  # no previous trades
        elif dbase.get_recent_high(pair, current_time, 12, 200):
            self.logger.info("Recently sold %s with high profit, skipping" % pair)
            able_to_open = False
        else:
            able_to_open = True

        trailing_perc = float(config.main.trailing_stop_loss_perc)
        high_price = self.get_drawup(pair)['price']
        low_price = self.get_drawdown(pair)
        trailing_stop = self.__get_trailing_stop(current_price, high_price, low_price,
                                                 res[0].high, res[0].low, res[0].open)
        take_profit_rule = self.__get_take_profit(current_price, res[0].high,
                                                  open_price, pair)

        stop_loss_rule = self.__get_stop_loss(current_price, res[0].low, open_price, pair)

        if any(rules['open']) and not able_to_open:
            self.logger.info("Unable to open trade %s due to time_between_trades" % pair)

        if open_price and any(rules['open']) and any(rules['close']):
            self.logger.warning('We ARE In a trade and have matched both open and '
                                'close rules for %s', pair)
            both = True
        elif not open_price and any(rules['open']) and any(rules['close']):
            self.logger.warning('We are NOT in a trade and have matched both open and '
                                'close rules for %s', pair)
            both = True
        else:
            both = False

        if stop_loss_rule and open_price:
            # if we match stop_loss rule and are in a trade

            if self.test_data and str2bool(config.main.immediate_stop):
                if config.main.trade_direction == 'short':
                    stop_at = add_perc(stop_loss_perc, open_price)
                    current_price = stop_at
                elif config.main.trade_direction == 'long':
                    stop_at = sub_perc(stop_loss_perc, open_price)
                    current_price = stop_at
            result = 'CLOSE'
            event = self.get_event_str("StopLoss" + result)

        elif trailing_stop and open_price:

            if self.test_data and str2bool(config.main.immediate_stop):
                if config.main.trade_direction == "long":
                    stop_at = sub_perc(trailing_perc, res[0].high)
                elif config.main.trade_direction == "short":
                    stop_at = add_perc(trailing_perc, res[0].low)
                current_price = stop_at
            result = 'CLOSE'
            event = self.get_event_str("TrailingStopLoss" + result)
        # if we match take_profit rule and are in a trade
        elif take_profit_rule and open_price:
            if self.test_data and str2bool(config.main.immediate_stop):
                stop_at = add_perc(take_profit_perc, open_price)
                current_price = stop_at

            result = 'CLOSE'
            event = self.get_event_str("TakeProfit" + result)

        elif close_timeout and close_timeout_price:
            result = 'CLOSE'
            event = self.get_event_str("TimeOut" + result)

        # if we match any close rules, are in a trade and no open rules match
        elif any(rules['close']) and open_price and not both:

            result = 'CLOSE'
            event = self.get_event_str("Normal" + result)

        # if we match any open rules are NOT in a trade and close rules don't match
        elif any(rules['open']) and not open_price and able_to_open and not both:

            # set stop_loss and take_profit
            self.update_on_entry(pair, 'take_profit_perc', eval(config.main.take_profit_perc))
            self.update_on_entry(pair, 'stop_loss_perc', eval(config.main.stop_loss_perc))

            # delete and re-store high price
            self.logger.debug("Close: %s, Previous Close: %s, >: %s" %
                              (res[0].close, res[1].close, res[0].close > res[1].close))

            result = 'OPEN'
            event = self.get_event_str("Normal" + result)

        elif open_price:
            result = 'HOLD'
            event = self.get_event_str(result)
        else:
            result = 'NOITEM'
            event = self.get_event_str(result)

        self.__log_event(pair=pair, event=event, current_time=current_time, data=str(res[0]))

        winning_close = self.__get_rules(rules, 'close')
        winning_open = self.__get_rules(rules, 'open')
        if winning_close:
            self.logger.info('%s close Rules matched: %s' % (pair, winning_close))
        else:
            self.logger.debug('%s close Rules matched: %s' % (pair, winning_close))
        if winning_open:
            self.logger.info('%s open Rules matched: %s' % (pair, winning_open))
        else:
            self.logger.debug('%s open Rules matched: %s' % (pair, winning_open))
        del dbase

        return (result, event, current_time, current_price, {'close':winning_close,
                                                             'open': winning_open})
