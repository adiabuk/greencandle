#pylint: disable=no-member,unused-variable,broad-except,unsubscriptable-object,eval-used
"""
Store and retrieve items from redis
"""
import os
import json
import time
import zlib
import pickle
from datetime import datetime, timedelta
import redis
from str2bool import str2bool
from greencandle.lib.mysql import Mysql
from greencandle.lib.logger import get_logger, exception_catcher
from greencandle.lib import config
from greencandle.lib.common import add_perc, sub_perc, perc_diff, convert_to_seconds, \
        get_short_name, epoch2date
from greencandle.lib.web import is_in_drain
from greencandle.lib.objects import AttributeDict, TF2MIN

GET_EXCEPTIONS = exception_catcher((Exception))

def get_float(var):
    """
    try to convert var into float
    otherwise return unmodified
    """
    try:
        return float(var)
    except ValueError:
        return var

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

        self.interval = interval
        self.test_data = test_data

        self.logger.debug("Starting Redis with interval %s db=%s", self.interval, db)
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
        redis1 = Redis(interval=self.interval, db=2)
        for key, val in data.items():
            self.logger.debug("Adding to Redis: %s %s %s", name, key, val)
            response = redis1.conn.hset(name, key, val)
        del redis1
        return response

    def get_drawup(self, pair, **kwargs):
        """
        Get maximum price of current open trade for given pair/interval
        and calculate drawdup based on trade opening price.
        Return max price and drawup as a percentage
        """

        name = kwargs['name'] if 'name' in kwargs else config.main.name
        direction = kwargs['direction'] if 'direction' in kwargs else config.main.trade_direction

        redis1 = Redis(interval=self.interval, db=2)

        short = get_short_name(name,
                               config.main.base_env,
                               direction)

        key = f"{pair}:drawup:{short}"
        max_price = redis1.get_item(key, 'max_price')
        orig_price = redis1.get_item(key, 'orig_price')
        try:
            drawup = perc_diff(orig_price, max_price)
        except TypeError:
            drawup = 0
        self.logger.debug("Getting %s drawup orig_price: %s,  max_price: %s, drawup: %s",
                          pair, orig_price, max_price, drawup)
        del redis1
        return {'price':max_price, 'perc': abs(drawup)}

    def rm_drawup(self, pair, **kwargs):
        """
        Delete current draw up value for given pair
        """
        redis1 = Redis(interval=self.interval, db=2)
        name = kwargs['name'] if 'name' in kwargs else config.main.name
        direction = kwargs['direction'] if 'direction' in kwargs else config.main.trade_direction

        short = get_short_name(name,
                               config.main.base_env,
                               direction)

        key = f"{pair}:drawup:{short}"
        redis1.conn.delete(key)
        del redis1

    def rm_drawdown(self, pair, **kwargs):
        """
        Delete current draw down value for given pair
        """
        redis1 = Redis(interval=self.interval, db=2)
        name = kwargs['name'] if 'name' in kwargs else config.main.name
        direction = kwargs['direction'] if 'direction' in kwargs else config.main.trade_direction

        short = get_short_name(name,
                               config.main.base_env,
                               direction)

        key = f"{pair}:drawdown:{short}"
        redis1.conn.delete(key)
        del redis1

    def get_drawdown(self, pair, **kwargs):
        """
        Get minimum price of current open trade for given pair/interval
        and calculate drawdown based on trade opening price.
        Return min price and drawdown as a percentage
        """

        name = kwargs['name'] if 'name' in kwargs else config.main.name
        direction = kwargs['direction'] if 'direction' in kwargs else config.main.trade_direction
        redis1 = Redis(interval=self.interval, db=2)

        short = get_short_name(name,
                               config.main.base_env,
                               direction)
        key = f"{pair}:drawdown:{short}"
        min_price = redis1.get_item(key, 'min_price')
        orig_price = redis1.get_item(key, 'orig_price')

        try:
            drawdown = perc_diff(orig_price, min_price)
        except TypeError:
            drawdown = 0
        self.logger.debug("Getting %s drawdown orig_price: %s,  min_price: %s, drawdown: %s",
                          pair, orig_price, min_price, drawdown)
        del redis1
        return {'price':min_price, 'perc': abs(drawdown)}

    def update_on_entry(self, pair, func, value,**kwargs):
        """
        Update key/value for storing profit/stoploss from figures derived at trade entry
        """
        redis1 = Redis(interval=self.interval, db=2)

        name = kwargs['name'] if 'name' in kwargs else config.main.name
        direction = kwargs['direction'] if 'direction' in kwargs else config.main.trade_direction

        short = get_short_name(name,
                               config.main.base_env,
                               direction)
        key = f"{pair}:{func}:{short}"
        if 'perc' in func:
            self.logger.info("Setting redis key %s to %s", key, value)
        redis1.conn.set(key, value)
        del redis1

    def get_on_entry(self, pair, func, **kwargs):
        """
        fetch key/value set on trade entry
        If no value exists, retrieve default from config
        Returns float
        """
        redis1 = Redis(interval=self.interval, db=2)
        name = kwargs['name'] if 'name' in kwargs else config.main.name
        direction = kwargs['direction'] if 'direction' in kwargs else config.main.trade_direction

        short = get_short_name(name,
                               config.main.base_env,
                               direction)
        key = f"{pair}:{func}:{short}"
        value = redis1.conn.get(key)

        self.logger.debug("getting key %s %s", key, value)
        try:
            result = float(value.decode())
        except AttributeError:
            result = float(config.main[func])
        del redis1
        return result

    def rm_on_entry(self, pair, name):
        """
        Remove key/value pair set at trade entry
        This is normally done on trade exit
        """
        redis1 = Redis(interval=self.interval, db=2)
        key = f"{pair}:{name}:{config.main.name}"
        return redis1.conn.delete(key)

    @staticmethod
    def in_current_candle(open_time):
        """
        Check we are still within the current candle
        If open_time + min(interval) is in the future
        """
        if not open_time:
            return False
        current_time = datetime.now()
        future_time = open_time + timedelta(minutes=TF2MIN[config.main.interval])
        return bool(future_time > current_time)

    def update_drawdown(self, pair, current_candle, event=None):
        """
        Update minimum price for current asset.  Create redis record if it doesn't exist.
        """
        redis1 = Redis(interval=self.interval, db=2)
        short = get_short_name(config.main.name,
                               config.main.base_env,
                               config.main.trade_direction)

        key = f"{pair}:drawdown:{short}"
        min_price = redis1.get_item(key, 'min_price')
        orig_price = redis1.get_item(key, 'orig_price')

        current_low = current_candle['low']
        current_high = current_candle['high']
        current_price = current_candle['close']

        if event == 'open':
            self.rm_drawdown(pair)
            current_low = current_price
            current_high = current_price
            min_price = None
            orig_price = None

        if not orig_price:
            orig_price = current_price

        if config.main.trade_direction == 'long':
            # if min price already exists and current price is lower, or there is no min price yet.
            price = current_price
            if (min_price and float(price) < float(min_price)) or not min_price:
                data = {"min_price": price, "orig_price": orig_price}
                self.logger.debug("setting drawdown for long %s", pair)
                self.__add_price(key, data)

        elif config.main.trade_direction == 'short':
            price = current_price
            if (min_price and float(price) > float(min_price)) or not min_price:
                data = {"min_price": price, "orig_price": orig_price}
                self.logger.debug("setting drawdown for short %s", pair)
                self.__add_price(key, data)

    def update_drawup(self, pair, current_candle, event=None):
        """
        Update maximum price for current asset.  Create redis record if it doesn't exist.
        """
        redis1 = Redis(interval=self.interval, db=2)
        short = get_short_name(config.main.name,
                               config.main.base_env,
                               config.main.trade_direction)
        key = f"{pair}:drawup:{short}"
        max_price = redis1.get_item(key, 'max_price')
        orig_price = redis1.get_item(key, 'orig_price')
        current_low = current_candle['low']
        current_high = current_candle['high']
        current_price = current_candle['close']

        if event == 'open':
            self.rm_drawup(pair)
            current_low = current_price
            current_high = current_price
            orig_price = None

        if not orig_price:
            orig_price = current_price

        if config.main.trade_direction == 'long':
            price = current_price
            if (max_price and float(price) > float(max_price)) or not max_price:
                data = {"max_price": price, "orig_price": orig_price}
                self.logger.debug("setting drawup for long %s", pair)
                self.__add_price(key, data)

        elif config.main.trade_direction == 'short':
            price = current_price
            if (max_price and float(price) < float(max_price)) or not max_price:
                data = {"max_price": price, "orig_price": orig_price}
                self.logger.debug("setting drawup for short %s", pair)
                self.__add_price(key, data)

    def append_data(self, pair, interval, data):
        """
        Add data to existing redis keys
        """
        date = data['event']['date']
        key = f"{pair}:{interval}"
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

        for close, value in data.items():
            key = f"{pair}:{interval}"
            expiry = int(config.redis.redis_expiry_seconds)
            value['current_epoch'] = int(time.time())
            value['current_time'] = epoch2date(time.time())
            result = self.conn.hmset(key, {close: json.dumps(value)})

        if expiry > 0:
            self.conn.expire(key, expiry)
        return result

    def get_intervals(self, pair, interval):
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
        key = f"{pair}:{interval}"
        return sorted([item.decode() for item in list(self.conn.hgetall(key).keys())])

    def get_item(self, address, key, pair=None, interval=None):
        """Return a specific item from redis, given an address and key"""
        if pair:
            try:
                item = json.loads(self.conn.hget(f"{pair}:{interval}",
                                                 address).decode())[key]
                return item
            except KeyError as keyerr:
                self.logger.warning("Unable to get key for %s %s: %s %s", pair, address,
                                    key, str(keyerr))
                return None
        item = self.conn.hget(address, key)
        return item

    def hgetall(self):
        """
        Log current redis hashes for debugging unit tests
        """
        for key in self.conn.keys():
            self.logger.critical("%s %s", key, self.conn.hgetall(key))

    def get_current(self, name, item, candle_type='ohlc'):
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
            data = json.loads(byte.decode("UTF-8"))[candle_type]
            current_price = data['close']
        except KeyError:
            self.logger.critical("No Data for item %s %s %s", name, item, candle_type)
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
            self.logger.debug("Running get_result %s %s %s %s", item, indicator, pair, interval)
            result = self.get_item(item, indicator, pair, interval)
        except AttributeError:
            return None

        try:
            return float(result)
        except TypeError:
            return result

    def __log_event(self, pair, event, current_time, data, agg):
        """Send event data to logger"""

        message = f'EVENT:({pair}) {event} time:{current_time} data:{data} agg:{agg}'

        if any(status in event for status in ['NOITEM', 'HODL']):
            self.logger.debug(message)
        else:
            self.logger.info(message)

    def get_intermittent(self, pair, open_price, current_candle, open_time):
        """
        Check if price between intervals and sell if matches stop_loss or take_profit rules
        """

        current_price = current_candle.close
        current_high = current_candle.high
        current_low = current_candle.low

        self.update_drawup(pair, current_candle)
        self.update_drawdown(pair, current_candle)
        high_price = self.get_drawup(pair)['price']
        low_price = self.get_drawdown(pair)['price']

        stop_loss_rule = self.__get_stop_loss(current_price, current_low, open_price, pair)

        take_profit_rule = self.__get_take_profit(current_price, current_high, open_price, pair)

        trailing_stop = self.__get_trailing_stop(low_price, high_price,  ohlc=(open_price,
                                                                          current_high,current_low,
                                                                          current_price))


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
                result = "HODL"
                event = self.get_event_str(result)
        else:
            result = "NOITEM"
            event = self.get_event_str(result)

        self.__log_event(pair=pair, event=event, current_time=current_time, data=0, agg=0)

        return (result, event, current_time, current_price)

    def __get_trailing_stop(self, low_price, high_price, ohlc=None):

        """
        Check if we have reached trailing stop loss
        return True/False
        """

        open_price, current_high, current_low, current_price = ohlc
        trailing_perc = float(config.main.trailing_stop_loss_perc)
        immediate = str2bool(config.main.immediate_trailing_stop)

        if trailing_perc <= 0:
            return False

        direction = config.main.trade_direction
        trailing_start = float(config.main.trailing_start)
        check = current_price
        if not high_price or not open_price:
            return False
        if direction == 'long' and self.test_data:
            check = current_high
        if direction == 'short' and self.test_data:
            check = current_low

        if direction == "long":
            result = float(check) <= sub_perc(float(trailing_perc), float(high_price)) and \
                    (self.test_data or float(current_price) > add_perc(float(trailing_start),
                                                                       float(open_price)))
        elif direction == "short":
            result = float(check) >= sub_perc(float(trailing_perc), float(low_price)) and \
                    (self.test_data or float(current_price) < sub_perc(float(trailing_start),
                                                                       float(open_price)))
        else:
            result = None

        if result:
            high_price = low_price if direction == "short" else high_price
            self.logger.info("TrailingStopLoss reached high_price: %s current_price: %s "
                             "open_price: %s", high_price, current_price, open_price)
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
        else:
            result = None
        return result

    def __get_take_profit(self, current_price, current_high, open_price, pair):
        """
        Check if we have reached take profit
        return True/False
        """

        profit_perc = self.get_on_entry(pair, 'take_profit_perc')
        if profit_perc <= 0:
            return False
        if is_in_drain():
            # override tp with drain tp if in drain
            profit_perc = config.main.drain_take_profit_perc

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
        else:
            self.logger.warning("invalid direction: %s", direction)
            return False

        if result:
            self.logger.info("TakeProfit reached current_high: %s current_price: %s "
                             "open_price: %s", current_high, current_price, open_price)
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
        if stop_perc <= 0:
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
        else:
            self.logger.warning("invalid direction: %s", direction)
            return False

        if result:
            self.logger.info("StopLoss reached current_low: %s current_price: %s "
                             "open_price: %s", current_low, current_price, open_price)
        return result

    @staticmethod
    def get_rules(rules, direction):
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
        return f"{trade_direction}_{trade_type}_{action}"

    def get_last_candle(self, pair, interval):
        """
        Get final reconstructed candle data
        """
        last_item = self.get_intervals(pair, interval)[-1]
        raw = self.get_current(f'{pair}:{interval}', last_item)
        try:
            return raw[-1]
        except Exception:  # hack for unit tests still using pickled zlib objects
            return pickle.loads(zlib.decompress(raw[-1]))

    def get_indicators(self, pair, interval, num=7):
        """
        get indicator data
        """
        res = []
        ind_list = []
        for i in config.main.indicators.split():
            split = i.split(';')
            ind = split[1]+'_' +split[2].split(',')[0]
            ind_list.append(ind)
        items = self.get_intervals(pair, interval)
        for i in range(-1, -(num), -1): # from, to, increment
            # look backwards through last x items of redis data
            datax = AttributeDict()
            for indicator in ind_list:
                datax[indicator] = self.get_result(items[i], indicator, pair, interval)
            name = f"{pair}:{interval}"
            ohlc = self.get_current(name, items[i])[-1]
            for item in ['open', 'high', 'low', 'close', 'volume']:
                ohlc[item] = float(ohlc[item])
            ha_raw = self.get_current(name, items[i], 'HA_0')[-1]
            if ha_raw:
                ha_ohlc={}
                for item in ['open', 'high', 'low', 'close']:
                    ha_ohlc[f'HA_{item}'] = float(ha_raw[item])
                datax.update(ha_ohlc)

            datax.update(ohlc)
            res.append(datax)

        return res, items

    @staticmethod
    def get_sentiment(pair, interval):
        """
        get sentiment from redis
        """
        redis15 = Redis(interval=interval, db=15)
        # get last 5 items in sentiment list and reverse
        raw_sent = redis15.conn.lrange(f'{pair}:{interval}',-5,-1)
        sent = [x.decode() for x in raw_sent]
        del redis15
        sent.reverse()

        return sent

    @staticmethod
    def get_agg_data(pair, interval):
        """
        fetch latest agg data and make available as AttributeDict
        """

        redis3 = Redis(interval=interval, db=3)
        raw = redis3.conn.hgetall(f'{pair}:{interval}')
        agg = AttributeDict({k.decode():get_float(v.decode()) for k, v in raw.items()})
        del redis3

        payload={'type':'agg', 'pair':pair, 'interval':interval, 'data':agg}
        return agg

    @GET_EXCEPTIONS
    def get_rule_action(self, pair, interval, check_reversal=False,
                        res=None, agg=None, sent=None, items=None):
        """
        get only rule results, without checking tp/sl etc.
        """

        # fetch latest agg data and make available as AttributeDict
        redis3 = Redis(interval=interval, db=3)
        raw = redis3.conn.hgetall(f'{pair}:{interval}')
        del redis3

        rules = {'open': [], 'close':[]}
        if not (res and items):
            res, items = self.get_indicators(pair, interval)
        else:
            res = [AttributeDict(x) for x in res]
        sent = self.get_sentiment(pair, interval) if not sent else sent
        agg = self.get_agg_data(pair, interval) if not agg else AttributeDict(agg)

        for seq in range(1, 6):
            current_config = None
            for rule in "open", "close":
                try:
                    current_config = config.main[f'{rule}_rule{seq}']
                except (KeyError, TypeError):
                    pass
                if current_config:
                    try:
                        rules[rule].append(eval(current_config))
                    except KeyError as error:
                        self.logger.warning("Unable to eval config rule for pair %s: %s_rule: %s "
                                            "%s mepoch: %s", pair, rule, current_config, error,
                                                               items[seq])
                        continue
                    except (ZeroDivisionError, TypeError) as error:
                        rules[rule].append(False)
                        self.logger.debug("Unable to eval config rule for pair %s: %s_rule: %s "
                                          "%s mepoch: %s", pair, rule, current_config, error,
                                          items[seq])
                        continue
        if config.main.base_env == "data" and not bool('STORE_IN_DB' in os.environ):
            open_price = None
        else:
            try:
                dbase = Mysql(interval=config.main.interval)
                open_price = dbase.get_trade_value(pair)[0][0]
                del  dbase
            except IndexError:
                open_price = None

        winning_open = self.get_rules(rules, 'open')
        winning_close = self.get_rules(rules, 'close')
        try:
            reversal = eval(config.main.reversal_rule) if check_reversal else False
        except TypeError:
            self.logger.warning("Unable to eval reversal rule for pair %s: rule: %s ",
                                pair, config.main.reversal_rule)
            reversal = False

        if any(rules['open']) and not open_price:
            result = 'OPEN'
        elif any(rules['close']) and open_price:
            result = 'CLOSE'
        else:
            result = 'HODL'
        event = self.get_event_str(result)

        current_epoch = int(items[-1])/1000
        current_price = float(res[0].close)
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(current_epoch))

        return result, event, current_time, current_price, {'close': winning_close,
                                                            'open': winning_open,
                                                            'reversal': reversal,
                                                            'res': res,
                                                            'agg': agg,
                                                            'sent': sent}
