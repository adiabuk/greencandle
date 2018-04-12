#pylint: disable=logging-format-interpolation

"""
Store and retrieve items from redis
"""

import ast
import time
import redis
from lib.mysql import Mysql
from lib.logger import getLogger

LOGGER = getLogger(__name__)

class Redis(object):
    """
    Redis object
    """

    def __init__(self, interval=None, host="localhost", port=6379, test=False, db=1):
        """
        Args:
            interval
            host
            port
            db
        returns:
            initialized redis connection
        """
        if test:
            redis_db = db
        else:
            redis_db = 0
        self.interval = interval
        LOGGER.debug("Starting Redis with interval %s", interval)
        pool = redis.ConnectionPool(host=host, port=port, db=redis_db)
        self.conn = redis.StrictRedis(connection_pool=pool)
        self.dbase = Mysql(test=test, interval=interval)

    def clear_all(self):
        """
        Wipe all data from redis - used for testing only
        """
        self.conn.execute_command("flushall")

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

    def get_current(self, item):
        """
        Get the current price and date for given item where item is an address:
        eg.  b"XRPBTC:15m:1520871299999"
        All items within a group should have the same date and price, as they relate to the same
        data - so we pick an indicator at random (RSI) to reference in the JSON that is stored.
        Returns:
            a tuple of current_price and current_date
        """

        byte = self.conn.hget(item, "RSI")
        data = ast.literal_eval(byte.decode("UTF-8"))

        return data["current_price"], data["date"]

    def get_change(self, pair, investment):
        """
        get recent change in pattern based on last 4 iterations for a given pair and interval
        Compute if we are in and overall BUY/SELL/HOLD scenario based on change in score over
        previous iterations.

        Return current total socre (int)
        """

        totals = []
        items = self.get_items(pair, self.interval)
        if len(items) < 3:
            LOGGER.info("insufficient items, skipping")
            return None, None
        for item in items[-4:]:
            totals.append(self.get_total(item))
        current = self.get_current(items[-1])
        current_price = current[0]
        current_mepoch = float(current[1])/1000
        LOGGER.debug("AMROX10 " + str(current[-1]) + " " + str(totals[-1]))
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(current_mepoch))
        value = self.dbase.get_trade_value(pair)

        if not value and (1 <= totals[-1] <= 50 and   # was -2 and 5
                          1 <= totals[-2] <= 50 and
                          float(sum(totals[:3])) / max(len(totals[:3]), 1) < totals[-1]):
            LOGGER.critical("AMROX8: BUY {0} {1} {2} {3}".format(totals, current_time,
                                                                 format(float(current_price),
                                                                        ".20f"),
                                                                 items[-1]))

            self.dbase.insert_trade(pair, current_time, format(float(current_price), ".20f"),
                                    investment, "0")
            return pair, None

        elif value and float(current_price) > (float(value[0]) *((8/100)+1)):
            LOGGER.critical("AMROX8: SELL {0} {1} {2} {3}".format(totals, current_time,
                                                                  format(float(current_price),
                                                                         ".20f"),
                                                                  items[-1]))
            self.dbase.update_trades(pair, current_time, format(float(current_price), ".20f"))
            return None, pair
        elif value and ((-20 <= totals[-1] <= -1 and
                         float(sum(totals[:3])) / max(len(totals[:3]), 1) > totals[-1]) and
                        float(current_price) > float(value[0]) or
                        float(current_price) > float(value[0]) * (2/100)+1):

            LOGGER.critical("AMROX8: SELL {0} {1} {2} {3}".format(totals, current_time,
                                                                  format(float(current_price),
                                                                         ".20f"),
                                                                  items[-1]))
            self.dbase.update_trades(pair, current_time, format(float(current_price), ".20f"))
            return "", ""
        return "", ""
        return totals
