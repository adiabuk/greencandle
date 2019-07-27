#pylint: disable=logging-format-interpolation,eval-used,no-else-return,unused-variable

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
from .config import get_config
from .common import add_perc, sub_perc
LOGGER = getLogger(__name__)
HOST = get_config("redis")["host"]
PORT = get_config("redis")["port"]

class AttributeDict(dict):
    """Access dictionary keys like attributes"""
    def __getattr__(self, attr):
        return self[attr]
    def __setattr__(self, attr, value):
        self[attr] = value

class Redis():
    """
    Redis object
    """

    def __init__(self, interval=None, test=False, db=1):
        """
        Args:
            interval
            host
            port
            db
        returns:
            initialized redis connection
        """
        LOGGER.debug("AMROX77 {0}".format(db))
        if test:
            redis_db = db
            test_str = "Test"
        else:
            redis_db = 0
            test_str = "Live"
        self.interval = interval
        self.test = test

        LOGGER.debug("Starting Redis with interval %s %s, db=%s", interval, test_str, str(redis_db))
        pool = redis.ConnectionPool(host=HOST, port=PORT, db=redis_db)
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

        LOGGER.info("Adding to Redis:{0} {1} {2}".format(interval, list(data.keys()), now))
        response = self.conn.hmset("{0}:{1}:{2}".format(pair, interval, now), data)
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
            LOGGER.error("No Data")
            return None, None

        return data["current_price"], data["date"], data['result']

    def get_action(self, pair, interval):

        results = AttributeDict(current=AttributeDict(), previous=AttributeDict(),
                                previous1=AttributeDict())
        try:
            previous1, previous, current = self.get_items(pair=pair, interval=interval)[-3:]
        except ValueError:
            return ('HOLD', 'Not enough data', 0)

        print(previous, current)
        # get current & previous indicator values
        main_indicators = get_config("backend")["indicators"].split()
        ind_list = []
        for i in main_indicators:
            split = i.split(';')
            ind = split[1] + '_' + split[2]
            ind_list.append(ind)

        for indicator in ind_list:

            results['current'][indicator] = ast.literal_eval(self.get_item( \
                    current, indicator).decode())['result']
            results['previous'][indicator] = ast.literal_eval(self.get_item( \
                    previous, indicator).decode())['result']
            results['previous1'][indicator] = ast.literal_eval(self.get_item( \
                    previous1, indicator).decode())['result']
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
        LOGGER.critical("Current OHLC: %s %s %s %s", open, high, low, close)
        LOGGER.critical("Previous OHLC: %s %s %s %s", last_open, last_high, last_low, last_close)
        current_price = float(current[0])
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(current_mepoch))

        buy_rules = []
        sell_rules = []
        for seq in range(1, 6):
            try:
                buy_rules.append(eval(get_config('backend')['buy_rule{}'.format(seq)]))
            except KeyError:
                pass
            try:
                sell_rules.append(eval(get_config('backend')['sell_rule{}'.format(seq)]))
            except KeyError:
                pass

        stop_loss_perc = float(get_config("backend")["stop_loss_perc"])
        take_profit_perc = float(get_config("backend")["take_profit_perc"])

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

        if stop_loss_rule:
            LOGGER.critical('stop_loss %s %s %s', buy_price, current_price, sub_perc(stop_loss_perc, buy_price))
        # if we have a buy_price (ie. currently in a trade) and
        # ether match all sell rules or at the stop loss amount
        if buy_price and (all(sell_rules) or stop_loss_rule):
            return ('SELL', current_time, current_price)

        # if we don't have a buy price (ie. not currently in a trade) and
        # either match all buy rules or at the take profit amount
        elif not buy_price and (all(buy_rules) or take_profit_rule):
            return ('BUY', current_time, current_price)
        else:
            return ('HOLD', current_time, current_price)

    def get_change(self, pair):
        """
        get recent change in pattern based on last 4 iterations for a given pair and interval
        Compute if we are in and overall BUY/SELL/HOLD scenario based on change in score over
        previous iterations.

        Return current total socre (int)
        """

        totals = []
        items = self.get_items(pair, self.interval)
        if len(items) < 3:
            LOGGER.warning("insufficient history for %s, skipping", pair)
            return None, None, None
        for item in items[-4:]:
            totals.append(self.get_total(item))

        current = self.get_current(items[-1])
        current_price = current[0]
        current_mepoch = float(current[1]) / 1000
        LOGGER.debug("AMROX10 %s %s %s ", pair, str(current[-1]), str(totals[-1]))
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(current_mepoch))
        value = self.dbase.get_trade_value(pair)

        if not value and (1 <= totals[-1] <= 50 and
                          1 <= totals[-2] <= 50 and
                          float(sum(totals[:3])) / max(len(totals[:3]), 1) < totals[-1]):
            LOGGER.critical("AMROX8: BUY {0} {1} {2} {3}".format(totals, current_time,
                                                                 format(float(current_price),
                                                                        ".20f"),
                                                                 items[-1]))

            #self.dbase.insert_trade(pair, current_time, format(float(current_price), ".20f"),
            #                        investment, "0")
            return "buy", current_time, format(float(current_price), ".20f")

        elif value and float(current_price) > (float(value[0][0]) *((8/100)+1)):
            # More than 8% over
            LOGGER.info("SELL 4% {0} {1} {2} {3}".format(totals, current_time,
                                                         format(float(current_price),
                                                                ".20f"),
                                                         items[-1]))
            return "sell", current_time, format(float(current_price), ".20f")

        elif value and ((-20 <= totals[-1] <= -1 and
                         float(sum(totals[:3])) / max(len(totals[:3]), 1) > totals[-1]) and
                        float(current_price) > float(value[0][0]) or
                        float(current_price) > float(value[0][0]) * (2/100)+1):
            # total is between -1 and -20 and
            # current_price is 2% more than buy price


            LOGGER.info("SELL 2% {0} {1} {2} {3}".format(totals, current_time,
                                                         format(float(current_price), ".20f"),
                                                         items[-1]))
            return "sell", current_time, format(float(current_price), ".20f")
        """ # FIXME
        elif value and float(current_price) < float(value[0][0]) * (1- (2/100)):  # 2% stop loss
            LOGGER.info("SELL stoploss {0} {1} {2} {3}".format(totals, current_time,
                                                               format(float(current_price), ".20f"),
                                                                items[-1]))
            return "sell" , current_time, format(float(current_price), ".20f")
        """
        return "hold", current_time, format(float(current_price), ".20f")
