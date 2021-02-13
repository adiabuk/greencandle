#pylint: disable=wrong-import-position,import-error,no-member,logging-not-lazy
#pylint: disable=wrong-import-order,no-else-return,no-else-break,no-else-continue
"""
Test Buy/Sell orders
"""

from __future__ import print_function
from collections import defaultdict
import time
from str2bool import str2bool
from binance import binance

from .auth import binance_auth
from .logger import get_logger, get_decorator
from .mysql import Mysql
from .redis_conn import Redis
from .binance_accounts import get_binance_values, get_binance_margin
from .balance_common import get_base, get_step_precision
from .common import perc_diff, add_perc, sub_perc, AttributeDict
from .alerts import send_gmail_alert, send_push_notif, send_slack_trade
from . import config
GET_EXCEPTIONS = get_decorator((Exception))

class InvalidTradeError(Exception):
    """
    Custom Exception for invalid trade type of trade direction
    """

class Trade():
    """Buy & Sell class"""

    def __init__(self, interval=None, test_data=False, test_trade=False):
        self.logger = get_logger(__name__)
        self.test_data = test_data
        self.test_trade = test_trade
        self.max_trades = int(config.main.max_trades)
        self.divisor = float(config.main.divisor) if config.main.divisor else None
        account = config.accounts.binance[0]
        binance_auth(account)

        self.interval = interval

    def __send_redis_trade(self, **kwargs):
        """
        Send trade event to redis
        """
        valid_keys = ["pair", "current_time", "price", "interval", "event"]
        kwargs = AttributeDict(kwargs)
        for key in valid_keys:
            if key not in valid_keys:
                raise KeyError("Missing param %s" % key)

        self.logger.debug('Strategy - Adding to redis')
        redis = Redis()
        # Change time back to milliseconds to line up with entries in redis
        mepoch = int(time.mktime(time.strptime(kwargs.current_time,
                                               '%Y-%m-%d %H:%M:%S'))) * 1000 + 999

        # if we are in an intermittent check - use previous timeframe
        if not str(mepoch).endswith('99999'):
            try:
                mepoch = redis.get_items(kwargs.pair, kwargs.interval)[-1].decode().split(':')[-1]
            except IndexError:
                self.logger.error("Unable to get last epoch time for %s %s" % (kwargs.pair,
                                                                               kwargs.interval))
                return

        data = {"event":{"result": kwargs.event,
                         "current_price": format(float(kwargs.price), ".20f"),
                         "date": mepoch,
                        }}

        redis.redis_conn(kwargs.pair, kwargs.interval, data, mepoch)
        del redis

    def amount_to_use(self, item, current_base_bal):
        """
        Figire out how much of current asset to buy based on balance and divisor
        """
        dbase = Mysql(test=self.test_data, interval=self.interval)
        try:
            last_open_price = dbase.fetch_sql_data("select base_in from trades where "
                                                   "pair='{0}' and name='{1}'".format(item,
                                                       config.main.name),
                                                   header=False)[-1][-1]
            last_open_price = float(last_open_price) if last_open_price else 0
        except IndexError:
            last_open_price = 0

        if self.divisor:
            proposed_base_amount = current_base_bal / self.divisor
        else:
            proposed_base_amount = current_base_bal / (self.max_trades + 1)
        self.logger.info('item: %s, proposed: %s, last:%s'
                         % (item, proposed_base_amount, last_open_price))

        if  last_open_price and last_open_price < current_base_bal:
            base_amount = max(proposed_base_amount, last_open_price)
        else:
            base_amount = proposed_base_amount

        return base_amount

    def check_pairs(self, items_list):
        """
        Check we can trade which each of given trading pairs
        Return filtered list
        """
        dbase = Mysql(test=self.test_data, interval=self.interval)
        current_trades = dbase.get_trades()
        drain = str2bool(config.main.drain)
        avail_slots = self.max_trades - len(current_trades)
        main_pairs = config.main.pairs
        self.logger.info("%s buy slots available" % avail_slots)
        if avail_slots <= 0:
            self.logger.warning("Too many trades, skipping")
            return []
        elif drain and not self.test_data:
            self.logger.warning("%s is in drain, skipping..." % self.interval)
            return []

        final_list = []
        for item in items_list:
            if current_trades and item[0] in current_trades[0]:
                self.logger.warning("We already have a trade of %s, skipping..." % item)
            elif item[0] not in main_pairs and not self.test_data:
                self.logger.warning("Pair %s not in main_pairs, skipping..." % item[0])
            else:
                final_list.append(item)
        return final_list

    def open_trade(self, items_list):
        """
        Main open trade method
        Will choose between spot/margin and long/short
        """
        items_list = self.check_pairs(items_list)
        if not items_list:
            self.logger.warning("No items to open trade with")
            return

        if config.main.trade_type == "spot":
            if config.main.trade_direction == "long":
                self.__open_spot_long(items_list)
            else:
                raise InvalidTradeError("Invalid trade direction for spot")

        elif config.main.trade_type == "margin":
            if config.main.trade_direction == "long":
                self.__open_margin_long(items_list)
            elif config.main.trade_direction == "short":
                self.__open_margin_short(items_list)
            else:
                raise InvalidTradeError("Invalid trade direction")

        else:
            raise InvalidTradeError("Invalid trade type")

    def close_trade(self, items_list, drawdowns=None, drawups=None):
        """
        Main close trade method
        Will choose between spot/margin and long/short
        """

        if not items_list:
            self.logger.warning("No items to close trade with")
            return

        if config.main.trade_type == "spot":
            if config.main.trade_direction == "long":
                self.__close_spot_long(items_list, drawdowns=drawdowns, drawups=drawups)
            else:
                raise InvalidTradeError("Invalid trade direction for spot")

        elif config.main.trade_type == "margin":
            if config.main.trade_direction == "long":
                self.__close_margin_long(items_list, drawdowns=drawdowns, drawups=drawups)
            elif config.main.trade_direction == "short":
                self.__close_margin_short(items_list, drawdowns=drawdowns, drawups=drawups)
            else:
                raise InvalidTradeError("Invalid trade direction")

        else:
            raise InvalidTradeError("Invalid trade type")

    def __open_margin_long(self, buy_list):
        """
        Buy as many items as we can from buy_list depending on max amount of trades, and current
        balance in base currency
        """
        self.logger.info("We have %s potential items to buy" % len(buy_list))

        prod = str2bool(config.main.production)

        dbase = Mysql(test=self.test_data, interval=self.interval)
        if self.test_data or self.test_trade:
            balance = self.__get_test_balance(dbase, account='margin')
        else:
            balance = get_binance_margin()

        for item, current_time, current_price, event in buy_list:
            base = get_base(item)
            try:
                current_base_bal = balance['margin'][base]['count']
            except KeyError:
                current_base_bal = 0
            base_amount = self.amount_to_use(item, current_base_bal)
            cost = current_price

            amount = base_amount / float(cost)
            if float(cost)*float(amount) >= float(current_base_bal):
                self.logger.critical("Unable to purchase %s of %s, insufficient funds:%s/%s" %
                                     (amount, item, base_amount, current_base_bal))
                continue
            else:
                self.logger.info("Buying %s of %s with %s %s"
                                 % (amount, item, base_amount, base))
                self.logger.debug("amount to buy: %s, cost: %s, amount:%s"
                                  % (base_amount, cost, amount))

                amount_to_borrow = float(base_amount) * float(config.main.multiplier)
                amount_to_use = sub_perc(5, amount_to_borrow)  # use 95% of borrowed funds

                self.logger.info("Will attempt to borrow %s of %s. Balance: %s"
                                 % (amount_to_borrow, base, base_amount))

                if prod:
                    borrow_result = binance.margin_borrow(base, amount_to_borrow)
                    if "msg" in borrow_result:
                        self.logger.error("Borrow error %s: %s" % (item, borrow_result))
                        return

                    self.logger.info(borrow_result)
                    amt_str = get_step_precision(item, amount_to_use/float(current_price))
                    trade_result = binance.margin_order(symbol=item, side=binance.BUY,
                                                        quantity=amt_str, isolated=False,
                                                        timeInForce='GTC',
                                                        order_type=binance.MARKET)
                    if "msg" in trade_result:
                        self.logger.error("Trade error %s: %s" % (item, str(trade_result)))
                        self.logger.error("Vars: quantity:%s, bal:%s" % (amt_str,
                                                                         current_base_bal))
                        return

                    base_amount = trade_result.get('cummulativeQuoteQty', base_amount)

                    prices = []
                    fill_price = cost


                    if 'transactTime' in trade_result:
                        # Get price from exchange
                        for fill in trade_result['fills']:
                            prices.append(float(fill['price']))
                        fill_price = sum(prices) / len(prices)
                        self.logger.info("Current price %s, Fill price: %s"
                                         % (cost, fill_price))


            if self.test_data or self.test_trade or \
                    (not self.test_trade and 'transactTime' in trade_result):

                dbase.insert_trade(pair=item, price=cost, date=current_time,
                                   base_amount=amount_to_use, quote=amt_str,
                                   borrowed=amount_to_borrow,
                                   multiplier=config.main.multiplier,
                                   direction=config.main.trade_direction)
                send_push_notif('BUY', item, '%.15f' % float(cost))
                send_gmail_alert('BUY', item, '%.15f' % float(cost))
                send_slack_trade(channel='trades', event=event, pair=item, action='open',
                                 price=cost)

                self.__send_redis_trade(pair=item, current_time=current_time, price=cost,
                                        interval=self.interval, event="BUY")
        del dbase

    @staticmethod
    @GET_EXCEPTIONS
    def __get_test_balance(dbase, account=None):
        """
        Get and return test balances
        """
        balance = defaultdict(lambda: defaultdict(defaultdict))

        balance[account]['BTC']['count'] = 0.15
        balance[account]['ETH']['count'] = 5.84
        balance[account]['USDT']['count'] = 1000
        balance[account]['USDC']['count'] = 1000
        balance[account]['BNB']['count'] = 14
        for base in ['BTC', 'ETH', 'USDT', 'BNB', 'USDC']:
            db_result = dbase.fetch_sql_data("select sum(base_out-base_in) from trades "
                                             "where pair like '%{0}'"
                                             .format(base), header=False)[0][0]
            db_result = float(db_result) if db_result else 0
            current_trade_values = dbase.fetch_sql_data("select sum(base_in) from trades "
                                                        "where pair like '%{0}' and "
                                                        "base_out is null"
                                                        .format(base), header=False)[0][0]
            current_trade_values = float(current_trade_values) if \
                    current_trade_values else 0
            balance[account][base]['count'] += db_result + current_trade_values
        return balance

    @GET_EXCEPTIONS
    def __open_spot_long(self, buy_list):
        """
        Buy as many items as we can from buy_list depending on max amount of trades, and current
        balance in base currency
        """
        self.logger.info("We have %s potential items to buy" % len(buy_list))

        prod = str2bool(config.main.production)

        dbase = Mysql(test=self.test_data, interval=self.interval)
        if self.test_data or self.test_trade:
            balance = self.__get_test_balance(dbase, account='binance')
        else:
            balance = get_binance_values()

        for item, current_time, current_price, event in buy_list:
            base = get_base(item)

            try:
                current_base_bal = balance['binance'][base]['count']
            except KeyError:
                current_base_bal = 0
            except TypeError:
                self.logger.critical("Unable to get balance for base %s while trading %s"
                                     % (base, item))
                self.logger.critical("complete balance: %s dict: %s" % (balance, current_base_bal))

            cost = current_price

            base_amount = self.amount_to_use(item, current_base_bal)
            amount = base_amount / float(cost)
            if float(cost)*float(amount) >= float(current_base_bal):
                self.logger.critical("Unable to purchase %s of %s, insufficient funds:%s/%s" %
                                     (amount, item, base_amount, current_base_bal))
                continue
            else:
                self.logger.info("Buying %s of %s with %s %s"
                                 % (amount, item, base_amount, base))
                self.logger.debug("amount to buy: %s, cost: %s, amount:%s"
                                  % (base_amount, cost, amount))
                if prod and not self.test_data:
                    amt_str = get_step_precision(item, amount)
                    if float(amt_str) <= 0:
                        self.logger.critical("Need more funds with given step_size")
                        return

                    trade_result = binance.spot_order(symbol=item, side=binance.BUY,
                                                      quantity=amt_str,
                                                      order_type=binance.MARKET,
                                                      test=self.test_trade)
                    if "msg" in trade_result:
                        self.logger.error("Trade error %s: %s" % (item, str(trade_result)))
                        self.logger.error("Vars: quantity:%s, bal:%s" % (amt_str,
                                                                         current_base_bal))
                        return

                    try:
                        # result empty if test_trade
                        cost = trade_result.get('fills', {})[0].get('price', cost)
                    except KeyError:
                        pass
                    base_amount = trade_result.get('cummulativeQuoteQty', base_amount)

                    prices = []
                    if 'transactTime' in trade_result:
                        # Get price from exchange
                        for fill in trade_result['fills']:
                            prices.append(float(fill['price']))
                        new_cost = sum(prices) / len(prices)
                        self.logger.info("Current price %s, Fill price: %s" % (cost, new_cost))
                        cost = new_cost
                else:
                    trade_result = True

                if self.test_data or self.test_trade or \
                        (not self.test_trade and 'transactTime' in trade_result):
                    # only insert into db, if:
                    # 1. we are using test_data
                    # 2. we performed a test trade which was successful - (empty dict)
                    # 3. we proformed a real trade which was successful - (transactTime in dict)
                    db_result = dbase.insert_trade(pair=item, price=cost, date=current_time,
                                                   base_amount=base_amount, quote=amount,
                                                   direction=config.main.trade_direction)
                    if db_result:
                        self.__send_redis_trade(pair=item, current_time=current_time, price=cost,
                                                interval=self.interval, event="BUY")
                        send_push_notif('BUY', item, '%.15f' % float(cost))
                        send_gmail_alert('BUY', item, '%.15f' % float(cost))
                        send_slack_trade(channel='trades', event=event, pair=item,
                                         action='open', price=cost)
        del dbase

    @GET_EXCEPTIONS
    def __close_margin_short(self, short_list, name=None, drawdowns=None, drawups=None):
        """
        Sell items in sell_list
        """

        prod = str2bool(config.main.production)
        self.logger.info("We need to close short %s" % short_list)
        dbase = Mysql(test=self.test_data, interval=self.interval)
        for item, current_time, current_price, event in short_list:
            quantity = dbase.get_quantity(item)
            if not quantity:
                self.logger.critical("Unable to find quantity for %s" % item)
                return
            price = current_price

            new_price = price  # for ci env - is overwritten in prod/stag
            buy_price, _, _, base_in, _ = dbase.get_trade_value(item)[0]
            perc_inc = perc_diff(buy_price, price)
            base_out = add_perc(perc_inc, base_in)

            send_gmail_alert("SELL", item, price)
            send_push_notif('SELL', item, '%.15f' % float(price))
            send_slack_trade(channel='trades', event=event, pair=item, action='close',
                             price=price, perc=perc_inc)

            self.logger.info("Closing %s of %s for %.15f %s"
                             % (quantity, item, float(price), base_out))
            if prod and not self.test_data:
                amt_str = get_step_precision(item, quantity)
                if float(amt_str) <= 0:
                    self.logger.critical("Need more funds with given step_size")
                    return

                trade_result = binance.spot_order(symbol=item, side=binance.SELL, quantity=amt_str,
                                                  order_type=binance.MARKET, test=self.test_trade)

                if "msg" in trade_result:
                    self.logger.error("Trade error %s: %s" % (item, trade_result))
                    return

                prices = []
                if 'transactTime' in trade_result:
                    # Get price from exchange
                    for fill in trade_result['fills']:
                        prices.append(float(fill['price']))
                    new_price = sum(prices) / len(prices)
                    self.logger.info("Current price %s, Fill price: %s" % (price, new_price))


            if self.test_data or (self.test_trade and not trade_result) or \
                    (not self.test_trade and 'transactTime' in trade_result):
                if name == "api":
                    name = "%"

                dbase.update_trades(pair=item, close_time=current_time,
                                    close_price=new_price, quote=quantity,
                                    base_out=base_out, name=name, drawdown=drawdowns[item],
                                    drawup=drawups[item])

                self.__send_redis_trade(pair=item, current_time=current_time, price=price,
                                        interval=self.interval, event="SELL")
            else:
                self.logger.critical("Sell Failed %s:%s" % (name, item))
        del dbase

    @GET_EXCEPTIONS
    def __open_margin_short(self, short_list):
        """
        bla bla bla
        """
        self.logger.info("We have %s potential items to short" % len(short_list))
        drain = str2bool(config.main.drain)
        if drain and not self.test_data:
            self.logger.warning("Skipping Buy as %s is in drain" % self.interval)
            return

        dbase = Mysql(test=self.test_data, interval=self.interval)

        if self.test_trade and not self.test_data:
            self.logger.error("Unable to perform margin short test without test data")

        for item, current_time, current_price, event in short_list:
            base = get_base(item)

            if self.test_data:
                base = get_base(item)
                prices = self.__get_test_balance(dbase, account='margin')
            try:
                current_base_bal = prices['margin'][base]['count']
            except KeyError:
                current_base_bal = 0

            proposed_quote_amount = self.amount_to_use(item, current_base_bal)
            base = get_base(item)
            cost = current_price

            amount_to_borrow = float(proposed_quote_amount) * float(config.main.multiplier)
            amount_to_use = sub_perc(5, amount_to_borrow)  # use 95% of borrowed funds

            amt_str = get_step_precision(item, amount_to_use)
            if float(amt_str) <= 0:
                self.logger.critical("Need more funds with given step_size")
                return

            base_amount = float(amt_str) * float(binance.prices()[item])

            dbase.insert_trade(pair=item, price=cost, date=current_time,
                               base_amount=base_amount,
                               quote=amt_str, borrowed=amount_to_borrow,
                               multiplier=config.main.multiplier,
                               direction=config.main.trade_direction)

            self.__send_redis_trade(pair=item, current_time=current_time, price=cost,
                                    interval=self.interval, event="BUY")
            send_gmail_alert("BUY", item, cost)
            send_push_notif('BUY', item, '%.15f' % float(cost))

            send_slack_trade(channel='trades', event=event, pair=item, action='open', price=cost)
            self.__send_redis_trade(pair=item, current_time=current_time, price=cost,
                                    interval=self.interval, event="BUY")

    @GET_EXCEPTIONS
    def __close_spot_long(self, sell_list, name=None, drawdowns=None, drawups=None):
        """
        Sell items in sell_list
        """

        prod = str2bool(config.main.production)
        self.logger.info("We need to sell %s" % sell_list)
        dbase = Mysql(test=self.test_data, interval=self.interval)
        for item, current_time, current_price, event in sell_list:
            quantity = dbase.get_quantity(item)
            if not quantity:
                self.logger.critical("Unable to find quantity for %s" % item)
                return
            price = current_price

            new_price = price  # for ci env - is overwritten in prod/stag
            buy_price, _, _, base_in, _ = dbase.get_trade_value(item)[0]
            perc_inc = perc_diff(buy_price, price)
            base_out = add_perc(perc_inc, base_in)


            self.logger.info("Selling %s of %s for %.15f %s"
                             % (quantity, item, float(price), base_out))
            if prod and not self.test_data:
                amt_str = get_step_precision(item, quantity)
                if float(amt_str) <= 0:
                    self.logger.critical("Need more funds with given step_size")
                    return

                trade_result = binance.spot_order(symbol=item, side=binance.SELL, quantity=amt_str,
                                                  order_type=binance.MARKET, test=self.test_trade)

                if "msg" in trade_result:
                    self.logger.error("Trade error %s: %s" % (item, trade_result))
                    return

                prices = []
                if 'transactTime' in trade_result:
                    # Get price from exchange
                    for fill in trade_result['fills']:
                        prices.append(float(fill['price']))
                    new_price = sum(prices) / len(prices)
                    self.logger.info("Current price %s, Fill price: %s" % (price, new_price))


            if self.test_data or self.test_trade or \
                    (not self.test_trade and 'transactTime' in trade_result):
                if name == "api":
                    name = "%"

                db_result = dbase.update_trades(pair=item, close_time=current_time,
                                                close_price=new_price, quote=quantity,
                                                base_out=base_out, name=name,
                                                drawdown=drawdowns[item],
                                                drawup=drawups[item])

                if db_result:
                    self.__send_redis_trade(pair=item, current_time=current_time, price=price,
                                            interval=self.interval, event="SELL")
                    send_gmail_alert("SELL", item, price)
                    send_push_notif('SELL', item, '%.15f' % float(price))
                    send_slack_trade(channel='trades', event=event, pair=item, action='close',
                                     price=price, perc=perc_inc)
            else:
                self.logger.critical("Sell Failed %s:%s" % (name, item))
        del dbase

    @GET_EXCEPTIONS
    def __close_margin_long(self, sell_list, name=None, drawdowns=None, drawups=None):
        """
        Sell items in sell_list
        """

        prod = str2bool(config.main.production)
        self.logger.info("We need to sell %s" % sell_list)
        dbase = Mysql(test=self.test_data, interval=self.interval)
        for item, current_time, current_price, event in sell_list:
            quantity = dbase.get_quantity(item)
            if not quantity:
                self.logger.critical("Unable to find quantity for %s" % item)
                return
            price = current_price
            open_price, quote_in, _, base_in, borrowed = dbase.get_trade_value(item)[0]
            perc_inc = perc_diff(open_price, price)
            base_out = add_perc(perc_inc, base_in)

            send_gmail_alert("SELL", item, price)
            send_push_notif('SELL', item, '%.15f' % float(price))
            send_slack_trade(channel='trades', event=event, pair=item, action='close',
                             price=price, perc=perc_inc)
            self.logger.info("Selling %s of %s for %.15f %s"
                             % (quantity, item, float(price), base_out))
            base = get_base(item)
            fill_price = price
            if prod:

                trade_result = binance.margin_order(symbol=item, side=binance.SELL,
                                                    quantity=quote_in, isolated=False,
                                                    timeInForce='GTC', order_type=binance.MARKET)

                if "msg" in trade_result:
                    self.logger.error("Trade error %s: %s" % (item, trade_result))
                    return

                repay_result = binance.margin_repay(base, borrowed)
                if "msg" in repay_result:
                    self.logger.error("Repay error %s: %s" % (item, repay_result))
                    return

                self.logger.info(repay_result)

                prices = []

                if 'transactTime' in trade_result:
                    # Get price from exchange
                    for fill in trade_result['fills']:
                        prices.append(float(fill['price']))
                    fill_price = sum(prices) / len(prices)
                    self.logger.info("Current price %s, Fill price: %s" % (price, fill_price))


            if self.test_data or self.test_trade or \
                    (not self.test_trade and 'transactTime' in trade_result):
                if name == "api":
                    name = "%"

                dbase.update_trades(pair=item, close_time=current_time,
                                    close_price=fill_price, quote=quantity,
                                    base_out=base_out, name=name, drawdown=drawdowns[item],
                                    drawup=drawups[item])

                self.__send_redis_trade(pair=item, current_time=current_time, price=price,
                                        interval=self.interval, event="SELL")
            else:
                self.logger.critical("Sell Failed %s:%s" % (name, item))
        del dbase
