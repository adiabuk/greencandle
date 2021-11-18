#pylint: disable=wrong-import-position,import-error,no-member,logging-not-lazy
#pylint: disable=wrong-import-order,no-else-return,no-else-break,no-else-continue
#pylint: disable=too-many-locals
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
from .binance_accounts import get_binance_values, get_binance_margin, get_current_isolated
from .balance_common import get_base, get_quote, get_step_precision
from .common import perc_diff, add_perc, sub_perc, AttributeDict
from .alerts import send_gmail_alert, send_push_notif, send_slack_trade, send_slack_message
GET_EXCEPTIONS = get_decorator((Exception))

class InvalidTradeError(Exception):
    """
    Custom Exception for invalid trade type of trade direction
    """

class Trade():
    """Buy & Sell class"""

    def __init__(self, interval=None, test_data=False, test_trade=False, config=None):
        self.logger = get_logger(__name__)
        self.test_data = test_data
        self.test_trade = test_trade
        self.config = config
        self.max_trades = int(self.config.main.max_trades)
        self.divisor = float(self.config.main.divisor) if self.config.main.divisor else None
        self.prod = str2bool(self.config.main.production)
        account = self.config.accounts.binance[0]
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
                self.logger.debug("Unable to get last epoch time for %s %s" % (kwargs.pair,
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
                                                   "pair='{0}' and name='{1}'"
                                                   .format(item, self.config.main.name),
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

        return proposed_base_amount

    def check_pairs(self, items_list):
        """
        Check we can trade which each of given trading pairs
        Return filtered list
        """
        dbase = Mysql(test=self.test_data, interval=self.interval)
        current_trades = dbase.get_trades()
        drain = str2bool(self.config.main.drain)
        avail_slots = self.max_trades - len(current_trades)
        self.logger.info("%s buy slots available" % avail_slots)
        if avail_slots <= 0:
            self.logger.warning("Too many trades, skipping")
            return []
        elif drain and not self.test_data:
            self.logger.warning("%s is in drain, skipping..." % self.interval)
            return []

        final_list = []
        manual = "manual" in self.config.main.name
        for item in items_list:
            if current_trades and item[0] in current_trades[0]:
                self.logger.warning("We already have a trade of %s, skipping..." % item[0])
            elif item[0] not in self.config.main.pairs and (not self.test_data or not manual):
                self.logger.error("Pair %s not in main_pairs, skipping..." % item[0])
            else:
                final_list.append(item)
        return final_list

    @GET_EXCEPTIONS
    def open_trade(self, items_list):
        """
        Main open trade method
        Will choose between spot/margin and long/short
        """
        items_list = self.check_pairs(items_list)
        if not items_list:
            self.logger.warning("No items to open trade with")
            return

        if self.config.main.trade_type == "spot":
            if self.config.main.trade_direction == "long":
                self.__open_spot_long(items_list)
            else:
                raise InvalidTradeError("Invalid trade direction for spot")

        elif self.config.main.trade_type == "margin":
            if self.config.main.trade_direction == "long":
                self.__open_margin_long(items_list)
            elif self.config.main.trade_direction == "short":
                self.__open_margin_short(items_list)
            else:
                raise InvalidTradeError("Invalid trade direction")

        else:
            raise InvalidTradeError("Invalid trade type")

    @GET_EXCEPTIONS
    def close_trade(self, items_list, drawdowns=None, drawups=None, update_db=True):
        """
        Main close trade method
        Will choose between spot/margin and long/short
        """
        additional_trades = []
        if not items_list:
            self.logger.warning("No items to close trade with")
            return
        else:

            for item in items_list:

                # Number of trades within scope
                dbase = Mysql(test=self.test_data, interval=self.interval)
                count = dbase.fetch_sql_data("select count(*) from trades where close_price "
                                             "is NULL and pair like '%{0}' and name='{1}'"
                                             .format(item[0], self.config.main.name),
                                             header=False)[0][0]

                while count -1 > 0:
                    additional_trades.append(item)
                    count -= 1

        items_list += additional_trades

        if self.config.main.trade_type == "spot":
            if self.config.main.trade_direction == "long":
                self.__close_spot_long(items_list, drawdowns=drawdowns, drawups=drawups,
                                       update_db=update_db)
            else:
                raise InvalidTradeError("Invalid trade direction for spot")

        elif self.config.main.trade_type == "margin":
            if self.config.main.trade_direction == "long":
                self.__close_margin_long(items_list, drawdowns=drawdowns, drawups=drawups)
            elif self.config.main.trade_direction == "short":
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

        dbase = Mysql(test=self.test_data, interval=self.interval)
        if self.test_data or self.test_trade:
            balance = self.__get_test_balance(dbase, account='margin')
        elif str2bool(self.config.main.isolated):
            balance = get_current_isolated()
        elif not str2bool(self.config.main.isolated):
            balance = get_binance_margin()

        for pair, current_time, current_price, event in buy_list:
            base = get_base(pair)
            try:
                if str2bool(self.config.main.isolated):
                    current_base_bal = float(balance[pair][base])
                else:
                    # Get current available to borrow
                    margin_total_usd = binance.get_max_borrow()

                    # Get current debts
                    for asset, debt in  binance.get_margin_debt().items():
                        # add debts to get total allowed to borrow
                        margin_total_usd += float(debt) if 'USD' in asset else \
                                float(debt) * float(binance.prices()[debt+'USDT'])
                    current_base_bal = margin_total_usd if base == 'USDT' else \
                            margin_total_usd / float(binance.prices()[base+"USDT"])

            except KeyError:
                current_base_bal = 0
            base_amount = self.amount_to_use(pair, current_base_bal)

            amount = base_amount / float(current_price)
            if float(current_price)*float(amount) >= float(current_base_bal):
                self.logger.critical("Unable to purchase %s of %s, insufficient funds:%s/%s" %
                                     (amount, pair, base_amount, current_base_bal))
                continue
            else:
                self.logger.info("Buying %s of %s with %s %s"
                                 % (amount, pair, base_amount, base))
                self.logger.debug("amount to buy: %s, current_price: %s, amount:%s"
                                  % (base_amount, current_price, amount))

                amount_to_borrow = float(base_amount) * float(self.config.main.multiplier)
                amount_to_use = sub_perc(1, amount_to_borrow)  # use 99% of borrowed funds

                self.logger.info("Will attempt to borrow %s of %s. Balance: %s"
                                 % (amount_to_borrow, base, base_amount))

                if self.prod:
                    borrow_res = binance.margin_borrow(symbol=pair, quantity=amount_to_borrow,
                                                       isolated=str2bool(self.config.main.isolated),
                                                       asset=base)
                    if "msg" in borrow_res:
                        self.logger.error("Borrow error-open %s: %s while trying to borrow %s %s"
                                          % (pair, borrow_res, amount_to_borrow, base))
                        continue

                    self.logger.info(borrow_res)
                    amt_str = get_step_precision(pair, amount_to_use/float(current_price))
                    trade_result = binance.margin_order(symbol=pair, side=binance.BUY,
                                                        quantity=amt_str,
                                                        order_type=binance.MARKET,
                                                        isolated=str2bool(
                                                            self.config.main.isolated))
                    if "msg" in trade_result:
                        self.logger.error("Trade error-open %s: %s" % (pair, str(trade_result)))
                        self.logger.error("Vars: quantity:%s, bal:%s" % (amt_str,
                                                                         current_base_bal))
                        continue

                    base_amount = trade_result.get('cummulativeQuoteQty', base_amount)
                    amt_str = trade_result.get('executedQty')
                else:
                    amt_str = amount_to_use

            fill_price = current_price if self.test_trade or self.test_data else \
                    self.__get_fill_price(current_price, trade_result)

            if self.test_data or self.test_trade or \
                    (not self.test_trade and 'transactTime' in trade_result):

                dbase.insert_trade(pair=pair, price=fill_price, date=current_time,
                                   base_amount=amount_to_use, quote=amt_str,
                                   borrowed=amount_to_borrow,
                                   multiplier=self.config.main.multiplier,
                                   direction=self.config.main.trade_direction, base=base)

                self.__send_notifications(pair=pair, current_time=current_time,
                                          fill_price=fill_price, interval=self.interval,
                                          event=event, action='OPEN', usd_profit='N/A')

        del dbase

    @GET_EXCEPTIONS
    def __get_test_balance(self, dbase, account=None):
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
                                             "where pair like '%{0}' and name='{1}'"
                                             .format(base, self.config.main.name),
                                             header=False)[0][0]
            db_result = float(db_result) if db_result and db_result > 0 else 0
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

        dbase = Mysql(test=self.test_data, interval=self.interval)
        if self.test_data or self.test_trade:
            balance = self.__get_test_balance(dbase, account='binance')
        else:
            balance = get_binance_values()

        for pair, current_time, current_price, event in buy_list:
            base = get_base(pair)

            try:
                current_base_bal = balance['binance'][base]['count']
            except KeyError:
                current_base_bal = 0
            except TypeError:
                self.logger.critical("Unable to get balance for base %s while trading %s"
                                     % (base, pair))
                self.logger.critical("complete balance: %s base_bal: %s"
                                     % (balance, current_base_bal))

            base_amount = self.amount_to_use(pair, current_base_bal)
            amount = base_amount / float(current_price)

            if float(current_price) * float(amount) > float(current_base_bal):
                self.logger.critical("Unable to purchase %s of %s, insufficient funds:%s/%s" %
                                     (amount, pair, base_amount, current_base_bal))
                continue
            else:
                self.logger.info("Buying %s of %s with %s %s"
                                 % (amount, pair, base_amount, base))
                self.logger.debug("amount to buy: %s, current_price: %s, amount:%s"
                                  % (base_amount, current_price, amount))
                if self.prod and not self.test_data:
                    amt_str = get_step_precision(pair, amount)

                    trade_result = binance.spot_order(symbol=pair, side=binance.BUY,
                                                      quantity=amt_str,
                                                      order_type=binance.MARKET,
                                                      test=self.test_trade)
                    if "msg" in trade_result:
                        self.logger.error("Trade error-open %s: %s" % (pair, str(trade_result)))
                        self.logger.error("Vars: quantity:%s, bal:%s" % (amt_str,
                                                                         current_base_bal))
                        return

                    base_amount = trade_result.get('cummulativeQuoteQty', base_amount)

                else:
                    trade_result = True

                fill_price = current_price if self.test_trade or self.test_data else \
                        self.__get_fill_price(current_price, trade_result)
                if self.test_data or self.test_trade or \
                        (not self.test_trade and 'transactTime' in trade_result):
                    # only insert into db, if:
                    # 1. we are using test_data
                    # 2. we performed a test trade which was successful - (empty dict)
                    # 3. we proformed a real trade which was successful - (transactTime in dict)
                    db_result = dbase.insert_trade(pair=pair, price=fill_price, date=current_time,
                                                   base_amount=base_amount, quote=amount,
                                                   direction=self.config.main.trade_direction,
                                                   base=base)
                    if db_result:
                        self.__send_notifications(pair=pair, current_time=current_time,
                                                  fill_price=fill_price, interval=self.interval,
                                                  event=event, action='OPEN', usd_profit='N/A')

        del dbase

    def __send_notifications(self, perc=None, **kwargs):
        """
        Pass given data to trade notification functions
        """
        valid_keys = ["pair", "current_time", "fill_price", "event", "action", "usd_profit"]
        kwargs = AttributeDict(kwargs)
        for key in valid_keys:
            if key not in valid_keys:
                raise KeyError("Missing param %s" % key)

        self.__send_redis_trade(pair=kwargs.pair, current_time=kwargs.current_time,
                                price=kwargs.fill_price, interval=self.interval,
                                event=kwargs.action, usd_profit=kwargs.usd_profit)
        send_push_notif(kwargs.action, kwargs.pair, '%.15f' % float(kwargs.fill_price))
        send_gmail_alert(kwargs.action, kwargs.pair, '%.15f' % float(kwargs.fill_price))
        send_slack_trade(channel='trades', event=kwargs.event, perc=perc,
                         pair=kwargs.pair, action=kwargs.action, price=kwargs.fill_price,
                         usd_profit=kwargs.usd_profit)

    def __get_fill_price(self, current_price, trade_result):
        """
        Extract and average trade result from exchange output
        """
        prices = []
        if 'transactTime' in trade_result:
            # Get price from exchange
            for fill in trade_result['fills']:
                prices.append(float(fill['price']))
            fill_price = sum(prices) / len(prices)
            self.logger.info("Current price %s, Fill price: %s" % (current_price, fill_price))
            return fill_price
        return None

    @GET_EXCEPTIONS
    def __close_margin_short(self, short_list, drawdowns=None, drawups=None):
        """
        Sell items in sell_list
        """

        self.logger.info("We need to close short %s" % short_list)
        dbase = Mysql(test=self.test_data, interval=self.interval)
        name = self.config.main.name
        for pair, current_time, current_price, event in short_list:
            quantity = dbase.get_quantity(pair)
            if not quantity:
                self.logger.info("close_margin_short: unable to find quantity for %s" % pair)
                return

            buy_price, _, _, base_in, _ = dbase.get_trade_value(pair)[0]
            perc_inc = -(perc_diff(buy_price, current_price))
            base_out = add_perc(perc_inc, base_in)

            self.logger.info("Closing %s of %s for %.15f %s"
                             % (quantity, pair, float(current_price), base_out))
            if self.prod and not self.test_data:
                amt_str = get_step_precision(pair, quantity)

                trade_result = binance.spot_order(symbol=pair, side=binance.SELL, quantity=amt_str,
                                                  order_type=binance.MARKET, test=self.test_trade)

                if "msg" in trade_result:
                    self.logger.error("Trade error-close %s: %s" % (pair, trade_result))
                    return

            fill_price = current_price if self.test_trade or self.test_data else \
                    self.__get_fill_price(current_price, trade_result)

            if self.test_data or self.test_trade or \
                    (not self.test_trade and 'transactTime' in trade_result):
                if name == "api":
                    name = "%"
                trade_id = dbase.update_trades(pair=pair, close_time=current_time,
                                               close_price=fill_price, quote=quantity,
                                               base_out=base_out, name=name,
                                               drawdown=drawdowns[pair], drawup=drawups[pair],
                                               base=get_base(pair))
                profit = dbase.fetch_sql_data("select usd_profit from profit "
                                              "where id={}".format(trade_id),
                                              header=False)[0][0]
                self.__send_notifications(pair=pair, current_time=current_time, perc=perc_inc,
                                          fill_price=current_price, interval=self.interval,
                                          event=event, action='CLOSE', usd_profit=profit)
            else:
                self.logger.critical("Sell Failed %s:%s" % (name, pair))
                send_slack_message("alerts", "Sell Failed %s:%s" % (name, pair))
        del dbase

    @GET_EXCEPTIONS
    def __open_margin_short(self, short_list):
        """
        open trades with items in short list
        """
        self.logger.info("We have %s potential items to short" % len(short_list))
        drain = str2bool(self.config.main.drain)
        if drain and not self.test_data:
            self.logger.warning("Skipping Buy as %s is in drain" % self.interval)
            return

        dbase = Mysql(test=self.test_data, interval=self.interval)

        for pair, current_time, current_price, event in short_list:
            base = get_base(pair)

            if self.test_data or self.test_trade:
                balance = self.__get_test_balance(dbase, account='margin')
            else:
                balance = get_binance_values()

            try:
                current_base_bal = balance['margin'][base]['count']
            except KeyError:
                current_base_bal = 0

            proposed_quote_amount = self.amount_to_use(pair, current_base_bal)

            amount_to_borrow = float(proposed_quote_amount) * float(self.config.main.multiplier)
            amount_to_use = sub_perc(1, amount_to_borrow)  # use 99% of borrowed funds

            amt_str = get_step_precision(pair, amount_to_use)

            base_amount = float(amt_str) * float(binance.prices()[pair])

            dbase.insert_trade(pair=pair, price=current_price, date=current_time,
                               base_amount=base_amount,
                               quote=amt_str, borrowed=amount_to_borrow,
                               multiplier=self.config.main.multiplier,
                               direction=self.config.main.trade_direction, base=base)

            self.__send_notifications(pair=pair, current_time=current_time,
                                      fill_price=current_price, interval=self.interval,
                                      event=event, action='OPEN', usd_profit='N/A')

    @GET_EXCEPTIONS
    def __close_spot_long(self, sell_list, drawdowns=None, drawups=None, update_db=True):
        """
        Sell items in sell_list
        """

        self.logger.info("We need to sell %s" % sell_list)
        dbase = Mysql(test=self.test_data, interval=self.interval)
        name = self.config.main.name
        for pair, current_time, current_price, event in sell_list:
            quantity = dbase.get_quantity(pair)
            if not quantity:
                self.logger.info("close_spot_long: unable to find quantity for %s" % pair)
                continue

            buy_price, _, _, base_in, _ = dbase.get_trade_value(pair)[0]
            perc_inc = perc_diff(buy_price, current_price)
            base_out = add_perc(perc_inc, base_in)

            self.logger.info("Selling %s of %s for %.15f %s"
                             % (quantity, pair, float(current_price), base_out))
            if self.prod and not self.test_data:

                # get amount from exchange
                ex_quantity = binance.my_trades(symbol=pair)[0]['qty']
                quantity = ex_quantity if float(ex_quantity) < float(quantity) else quantity

                amt_str = get_step_precision(pair, quantity)

                trade_result = binance.spot_order(symbol=pair, side=binance.SELL, quantity=amt_str,
                                                  order_type=binance.MARKET, test=self.test_trade)

                if "msg" in trade_result:
                    self.logger.error("Trade error-close %s: %s" % (pair, trade_result))
                    continue

            fill_price = current_price if self.test_trade or self.test_data else \
                    self.__get_fill_price(current_price, trade_result)

            if self.test_data or self.test_trade or \
                    (not self.test_trade and 'transactTime' in trade_result):
                if name == "api":
                    name = "%"

                if update_db:
                    trade_id = dbase.update_trades(pair=pair, close_time=current_time,
                                                   close_price=fill_price, quote=quantity,
                                                   base_out=base_out, name=name,
                                                   drawdown=drawdowns[pair],
                                                   drawup=drawups[pair], base=get_base(pair))
                    profit = dbase.fetch_sql_data("select usd_profit from profit "
                                                  "where id={}".format(trade_id),
                                                  header=False)[0][0]
                    self.__send_notifications(pair=pair, current_time=current_time, perc=perc_inc,
                                              fill_price=fill_price, interval=self.interval,
                                              event=event, action='CLOSE', usd_profit=profit)
            else:
                self.logger.critical("Sell Failed %s:%s" % (name, pair))
                send_slack_message("alerts", "Sell Failed %s:%s" % (name, pair))
        del dbase

    @GET_EXCEPTIONS
    def __close_margin_long(self, sell_list, drawdowns=None, drawups=None):
        """
        Sell items in sell_list
        """

        self.logger.info("We need to sell %s" % sell_list)
        dbase = Mysql(test=self.test_data, interval=self.interval)
        name = self.config.main.name
        for pair, current_time, current_price, event in sell_list:
            quantity = dbase.get_quantity(pair)
            if not quantity:
                self.logger.info("close_margin_long: unable to find quantity for %s" % pair)
                continue
            open_price, _, _, base_in, borrowed = dbase.get_trade_value(pair)[0]
            perc_inc = perc_diff(open_price, current_price)
            base_out = add_perc(perc_inc, base_in)

            self.logger.info("Selling %s of %s for %.15f %s"
                             % (quantity, pair, float(current_price), base_out))
            base = get_base(pair)

            if self.prod:
                # get amount from exchange
                ex_quantity = binance.my_margin_trades(pair, str2bool(self.config.main.isolated))[0]['qty']
                quantity = ex_quantity if float(ex_quantity) < float(quantity) else quantity

                amt_str = get_step_precision(pair, quantity)

                trade_result = binance.margin_order(symbol=pair, side=binance.SELL,
                                                    quantity=amt_str,
                                                    order_type=binance.MARKET,
                                                    isolated=str2bool(
                                                        self.config.main.isolated))

                if "msg" in trade_result:
                    self.logger.error("Trade error-close %s: %s" % (pair, trade_result))
                    continue

                repay_result = binance.margin_repay(symbol=pair, quantity=borrowed,
                                                    isolated=str2bool(self.config.main.isolated),
                                                    asset=base)
                if "msg" in repay_result:
                    self.logger.error("Repay error-close %s: %s" % (pair, repay_result))
                    continue

                self.logger.info(repay_result)

            fill_price = current_price if self.test_trade or self.test_data else \
                    self.__get_fill_price(current_price, trade_result)

            if self.test_data or self.test_trade or \
                    (not self.test_trade and 'transactTime' in trade_result):
                if name == "api":
                    name = "%"

                trade_id = dbase.update_trades(pair=pair, close_time=current_time,
                                               close_price=fill_price, quote=quantity,
                                               base_out=base_out, name=name,
                                               drawdown=drawdowns[pair],
                                               drawup=drawups[pair], base=base)


                profit = dbase.fetch_sql_data("select usd_profit from profit "
                                              "where id={}".format(trade_id), header=False)[0][0]
                self.__send_notifications(pair=pair, current_time=current_time, perc=perc_inc,
                                          fill_price=fill_price, interval=self.interval,
                                          event=event, action='CLOSE', usd_profit=profit)
            else:
                self.logger.critical("Sell Failed %s:%s" % (name, pair))
                send_slack_message("alerts", "Sell Failed %s:%s" % (name, pair))
        del dbase
