#pylint: disable=eval-used,no-else-return,unused-variable,no-member

"""
Store and retrieve items from redis
"""
import ast
import time
import zlib
import pickle
import redis
from .mysql import Mysql
from .logger import getLogger
from . import config
from .common import add_perc, sub_perc, AttributeDict

class Redis():
    """
    Redis object
    """

    def __init__(self, interval=None, test=False, db=1, expire=True):
        """
        Args:
            interval
            host
            port
            db
        returns:
            initialized redis connection
        """
        self.logger = getLogger(__name__, config.main.logging_level)
        self.host = config.redis.host
        self.port = config.redis.port
        self.expire = str2bool(config.redis.expire)

        if test:
            redis_db = db
            test_str = "Test"
        else:
            redis_db = 0
            test_str = "Live"
        self.interval = interval
        self.test = test

        self.logger.debug("Starting Redis with interval %s %s, db=%s", interval,
                          test_str, str(redis_db))
        pool = redis.ConnectionPool(host=self.host, port=self.port, db=redis_db)
        self.conn = redis.StrictRedis(connection_pool=pool)
        self.dbase = Mysql(test=test, interval=interval)

    def __del__(self):
        del self.dbase

    def clear_all(self):
        """
        Wipe all data current redis db - used for testing only
        """
        self.conn.execute_command("flushdb")

    def redis_conn(self, pair, interval, data, now):
        """
        Add data to redis

        Args:
              pair: trading pair (eg. XRPBTC)
              interval: interval of each kline
              data: json with data to store
              now: datatime stamp
        Returns:
            success of operation: True/False
        """

        self.logger.info("Adding to Redis: %s %s %s", interval, list(data.keys()), now)
        key = "{0}:{1}:{2}".format(pair, interval, now)
        expiry = 600 if self.test else 18000
        response = self.conn.hmset(key, data)
        if self.expire:
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

    def get_details(self, address):
        """
        Get totals of results in each group

        Args:
              address
              eg.  b"XRPBTC:15m:1520869499999",
        """
        return self.conn.hgetall(address).items()

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
            self.logger.error("No Data")
            return None, None

        return data["current_price"], data["date"], data['result']

    def get_result(self, item, indicator):
        """Retrive decoded OHLC data from redis"""
        try:
            return ast.literal_eval(self.get_item(item, indicator).decode())['result']
        except AttributeError:
            return None

    def log_event(self, event, rate, buy, sell, pair, current_time):
        """Send event data to logger"""
        self.logger.info('EVENT:(%s) %s rate:%s buy:%s sell:%s, time:%s',
                         pair, event, format(float(rate), ".2f"), buy, sell, current_time)

    def get_action(self, pair, interval):
        """Determine if we are in a BUY/HOLD/SELL situration for a specific pair and interval"""
        results = AttributeDict(current=AttributeDict(), previous=AttributeDict(),
                                previous1=AttributeDict())
        try:
            previous1, previous, current = self.get_items(pair=pair, interval=interval)[-3:]
        except ValueError:
            return ('HOLD', 'Not enough data', 0)

        # get current & previous indicator values
        main_indicators = config.main.indicators.split()

        ind_list = []
        for i in main_indicators:
            split = i.split(';')
            ind = split[1] + '_' + split[2]
            ind_list.append(ind)

        for indicator in ind_list:
            results['current'][indicator] = self.get_result(current, indicator)
            results['previous'][indicator] = self.get_result(previous, indicator)
            results['previous1'][indicator] = self.get_result(previous1, indicator)
        items = self.get_items(pair, self.interval)
        current = self.get_current(items[-1])
        previous = self.get_current(items[-2])
        current_mepoch = float(current[1]) / 1000



        rehydrated = pickle.loads(zlib.decompress(current[-1]))
        last_rehydrated = pickle.loads(zlib.decompress(previous[-1]))

        # variables that can be referenced in config file
        open = rehydrated.open
        high = rehydrated.high
        low = rehydrated.low
        close = rehydrated.close
        last_open = last_rehydrated.open
        last_high = last_rehydrated.high
        last_low = last_rehydrated.low
        last_close = last_rehydrated.close

        current_price = float(close)
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(current_mepoch))


        # rate of Moving Average increate/decreate based on indicator
        # specified in the rate_indicator config option - best with EMA_200
        rate_indicator = config.main.rate_indicator
        rate = str(float(results.current[rate_indicator]) - float(results.previous[rate_indicator]))
        last_rate = str(float(results.previous[rate_indicator]) - \
                float(results.previous1[rate_indicator]))

        buy_rules = []
        sell_rules = []
        for seq in range(1, 10):
            try:
                buy_rules.append(eval(config.main['buy_rule{}'.format(seq)]))
            except (KeyError, TypeError):
                pass
            try:
                sell_rules.append(eval(config.main['sell_rule{}'.format(seq)]))
            except KeyError:
                pass
            except TypeError as error:
                self.logger.warning("Failed to eval sell rule: %s", error)

        stop_loss_perc = float(config.main["stop_loss_perc"])
        take_profit_perc = float(config.main["take_profit_perc"])

        try:
            # function returns an empty list if no results so cannot get first element
            buy_price = float(self.dbase.get_trade_value(pair)[0][0])
            stop_loss_rule = current_price < sub_perc(stop_loss_perc, buy_price)
            take_profit_rule = current_price > add_perc(take_profit_perc, buy_price)

        except (IndexError, ValueError):
            # Setting to none to indicate we are currently not in a trade
            buy_price = None
            stop_loss_rule = False
            take_profit_rule = False

        # if we match stop_loss rule and are in a trade
        if stop_loss_rule and buy_price:
            self.log_event('StopLoss', rate, buy_price, sub_perc(stop_loss_perc, buy_price),
                           pair, current_time)
            return ('SELL', current_time, current_price)
        # if we match take_profit rule and are in a trade
        elif take_profit_rule and buy_price:
            self.log_event('TakeProfit', rate, buy_price, current_price, pair, current_time)
            return ('SELL', current_time, current_price)
        # if we match any sell rules and are in a trade
        elif any(sell_rules) and buy_price:

            self.log_event('NormalSell', rate, buy_price, current_price, pair, current_time)
            return ('SELL', current_time, current_price)
        # if we match all buy rules and are NOT in a trade
        elif all(buy_rules) and not buy_price:
            self.log_event('NormalBuy', rate, current_price, current_price, pair, current_time)
            return ('BUY', current_time, current_price)
        elif buy_price:
            self.log_event('Hold', rate, buy_price, current_price, pair, current_time)
            return ('HOLD', current_time, current_price)
        else:
            return ('NOITEM', current_time, current_price)
