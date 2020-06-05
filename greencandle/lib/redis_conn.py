#pylint: disable=eval-used,no-else-return,unused-variable,no-member,redefined-builtin

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

        self.logger.debug("Starting Redis with interval %s %s, db=%s", interval,
                          test_str, str(db))
        pool = redis.ConnectionPool(host=self.host, port=self.port, db=db)
        self.conn = redis.StrictRedis(connection_pool=pool)

    def __del__(self):
        del self.conn

    def clear_all(self):
        """
        Wipe all data current redis db - used for testing only
        """
        self.conn.execute_command("flushdb")

    def add_min_price(self, pair, data):
        """
        add/update min price dict
        """
        for key, val in data.items():

            self.logger.debug("Adding to Redis: %s %s %s", pair, key, val)
            response = self.conn.hset(pair, key, val)
        return response

    def rm_min_price(self, pair):
        """
        Remove current min_price
        """
        result = self.conn.delete(pair)

    def put_high_price(self, pair, interval, price):
        """
        update high price if current price is
        higher then previously stored value
        """
        key = 'highClose_{0}_{1}'.format(pair, interval)

        last_price = self.conn.get(key)
        if not last_price or float(price) > float(last_price):
            result = self.conn.set(key, price)
            self.logger.debug("Setting high price for %s, result:%s", pair, result)

    def get_high_price(self, pair, interval):
        """get current highest price for pair and interval"""
        key = 'highClose_{0}_{1}'.format(pair, interval)
        try:
            last_price = float(self.conn.get(key))
        except TypeError:
            last_price = None
        return last_price

    def del_high_price(self, pair, interval):
        """Delete highest price in redis"""
        key = 'highClose_{0}_{1}'.format(pair, interval)
        result = self.conn.delete(key)
        self.logger.debug("Deleting high price for %s, result:%s", pair, result)


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

        self.logger.debug("Adding to Redis: %s %s %s", interval, list(data.keys()), now)
        key = "{0}:{1}:{2}".format(pair, interval, now)
        expiry = int(config.redis.redis_expiry_seconds)

        for k, v in data.items():
            response = self.conn.hset(key, k, v)

        if self.expire:
            self.conn.expire(key, expiry)

        return response

    def del_key(self, key):
        """
        delete a given entry
        """
        result = self.conn.delete(key)
        self.logger.debug("Deleting key %s, result:%s", key, result)

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
            self.logger.error("No Data")
            return None, None

        return data["current_price"], data["date"], data['result']

    def get_result(self, item, indicator):
        """Retrive decoded OHLC data from redis"""
        try:
            return float(ast.literal_eval(self.get_item(item, indicator).decode())['result'])
        except (TypeError, AttributeError):
            return None


    def log_event(self, event, rate, perc_rate, buy, sell, pair, current_time, current):
        """Send event data to logger"""
        message = 'EVENT:({0}) {1} rate:{2} perc_rate:{3} buy:{4} sell:{5}, time:{6}'.format(
            pair, event, format(float(rate), ".4f"), format(float(perc_rate), ".4f"),
            buy, sell, current_time)

        if event == "Hold":
            self.logger.debug(message)
        else:
            self.logger.info(message)
        self.logger.debug("%s, %s", message, current)

    def get_intermittant(self, pair, buy_price, current_price):
        """
        Check if price between intervals and sell if matches stop_loss or take_profit rules
        """

        stop_loss_perc = float(config.main.stop_loss_perc)
        take_profit_perc = float(config.main.take_profit_perc)
        stop_loss_rule = float(current_price) < sub_perc(stop_loss_perc, buy_price)
        take_profit_rule = float(current_price) > add_perc(take_profit_perc, buy_price)
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())

        if stop_loss_rule and buy_price:
            message = "StopLoss intermittant"
            self.logger.info(message)
            return ('SELL', current_time, current_price)
        elif str2bool(config.main.take_profit) and take_profit_rule and buy_price:
            message = "TakeProfit intermittant"
            self.logger.info(message)
            return ('SELL', current_time, current_price)
        else:
            return ('HOLD', current_time, current_price)

    @staticmethod
    def get_rules(rules, direction):
        """determine which rules have been matched"""
        winning = []
        for seq, sell_rule in enumerate(rules[direction]):
            if sell_rule:
                winning.append(seq + 1)
        return winning

    def get_action(self, pair, interval, test_data=False):
        """Determine if we are in a BUY/HOLD/SELL situration for a specific pair and interval"""
        results = AttributeDict(current=AttributeDict(), previous=AttributeDict(),
                                previous1=AttributeDict(), previous2=AttributeDict(),
                                previous3=AttributeDict())
        try:
            previous3, previous2, previous1, previous, current = \
                    self.get_items(pair=pair, interval=interval)[-5:]
        except ValueError:

            self.logger.debug("Not enough data for %s", pair)
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
            buy_price = float(dbase.get_trade_value(pair)[0][0])
        except IndexError:
            buy_price = None



        current_price = float(close)
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime(current_epoch))

        # Store/update highest price
        self.put_high_price(pair, interval, current_price)

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

        rules = {'buy': [], 'sell': []}
        for seq in range(1, 10):
            current_config = None
            for rule in "buy", "sell":
                try:
                    current_config = config.main['{}_rule{}'.format(rule, seq)]
                    self.logger.debug("Rule: %s_rule%s: %s", rule, seq, current_config)
                except (KeyError, TypeError):
                    pass
                if current_config:
                    try:
                        rules[rule].append(eval(current_config))
                    except (TypeError, KeyError) as error:
                        self.logger.warning("Unable to eval config rule: %s_rule: %s %s",
                                            rule, current_config, error)
                        continue

        stop_loss_perc = float(config.main.stop_loss_perc)
        take_profit_perc = float(config.main.take_profit_perc)
        able_to_buy = True

        if not buy_price and str2bool(config.main.wait_between_trades):
            try:
                buy_time = dbase.fetch_sql_data("select sell_time from trades where pair='{}' "
                                                "and closed_by = 'api' order by sell_time desc "
                                                "LIMIT 1", header=False)[0][0]
                buy_epoch = 0 if not isinstance(buy_time, datetime) else \
                    buy_time.timestamp()
                pattern = '%Y-%m-%d %H:%M:%S'
                buy_epoch = buy_time.timestamp()
                able_to_buy = (int(buy_epoch) +
                               int(convert_to_seconds(config.main.time_between_trades))) < \
                               current_epoch
            except (IndexError, AttributeError):
                pass  # no previous trades
        else:
            able_to_buy = True

        try:
            # function returns an empty list if no results so cannot get first element
            buy_price = float(dbase.get_trade_value(pair)[0][0])

            if str2bool(config.main.trailing_stop_loss):
                high_price = self.get_high_price(pair, interval)
                take_profit_price = add_perc(take_profit_perc, buy_price)

                trailing_perc = float(config.main.trailing_stop_loss_perc)
                if high_price:
                    trailing_stop = current_price <= sub_perc(trailing_perc, high_price)

                else:
                    trailing_stop = False
            else:
                trailing_stop = False
                high_price = buy_price

            stop_loss_rule  = current_price < sub_perc(stop_loss_perc, buy_price)

            take_profit_rule = current_price > add_perc(take_profit_perc, buy_price)

        except (IndexError, ValueError):
            # Setting to none to indicate we are currently not in a trade
            buy_price = None
            stop_loss_rule = False
            take_profit_rule = False
            trailing_stop = False


        if buy_price and any(rules['buy']) and any(rules['sell']):
            self.logger.warning('We ARE In a trade and have matched both buy and '
                                'sell rules for %s', pair)
            both = True
        elif not buy_price and any(rules['buy']) and any(rules['sell']):
            self.logger.warning('We are NOT in a trade and have matched both buy and '
                                'sell rules for %s', pair)
            both = True
        else:
            both = False

        # if we match stop_loss rule and are in a trade
        if stop_loss_rule and buy_price:
            self.logger.warning("StopLoss: buy_price:%s high_price:%s", buy_price, high_price)
            stop_at = sub_perc(stop_loss_perc, buy_price)
            self.log_event('StopLoss', rate, perc_rate, buy_price,
                           stop_at, pair, current_time, results.current)
            self.del_high_price(pair, interval)
            if test_data:
                # with test data we don't check between candles so frequently skip over the
                # stop-loss value.  As a test workaround we will set the current price to the price
                # where we would have exited the trade in order to have test results that mimic what
                # we would see in production
                current_price = stop_at
            result = 'SELL'
        elif trailing_stop and buy_price:
            stop_at = sub_perc(trailing_perc, high_price)
            self.logger.info("TrailingStopLoss: buy_price:%s high_price:%s", buy_price, high_price)
            self.logger.info("Trailing stop loss reached")
            self.log_event('TrailingStopLoss', rate, perc_rate, buy_price,
                           stop_at, pair, current_time, results.current)
            self.del_high_price(pair, interval)

            if test_data:
                current_price = stop_at
            result = 'SELL'

        # if we match take_profit rule and are in a trade
        elif str2bool(config.main.take_profit) and take_profit_rule and buy_price:
            self.log_event('TakeProfit', rate, perc_rate, buy_price, current_price,
                           pair, current_time, results.current)
            self.del_high_price(pair, interval)
            result = 'SELL'

        # if we match any sell rules, are in a trade and no buy rules match
        elif any(rules['sell']) and buy_price and not both:

            self.log_event('NormalSell', rate, perc_rate, buy_price, current_price,
                           pair, current_time, results.current)

            self.del_high_price(pair, interval)
            result = 'SELL'

        # if we match any buy rules are NOT in a trade and sell rules don't match
        elif any(rules['buy']) and not buy_price and able_to_buy and not both:
            self.log_event('NormalBuy', rate, perc_rate, current_price, current_price,
                           pair, current_time, results.current)

            # delete and re-store high price
            self.del_high_price(pair, interval)
            self.put_high_price(pair, interval, current_price)
            self.logger.debug("Close: %s, Previous Close: %s, >: %s",
                              close, last_close, close > last_close)
            result = 'BUY'

        elif buy_price:
            self.log_event('Hold', rate, perc_rate, buy_price, current_price, current_time,
                           pair, results.current)
            result = 'HOLD'
        else:
            result = 'NOITEM'


        winning_sell = self.get_rules(rules, 'sell')
        winning_buy = self.get_rules(rules, 'buy')
        self.logger.info('%s sell Rules matched: %s', pair, winning_sell)
        self.logger.info('%s buy Rules matched: %s', pair, winning_buy)
        del dbase
        return (result, current_time, current_price, {'sell':winning_sell,
                                                      'buy': winning_buy})
