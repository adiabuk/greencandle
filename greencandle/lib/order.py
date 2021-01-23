#pylint: disable=wrong-import-position,import-error,no-member,logging-not-lazy
#pylint: disable=wrong-import-order,no-else-return,no-else-break,no-else-continue
"""
Test Buy/Sell orders
"""

from __future__ import print_function
from collections import defaultdict
from str2bool import str2bool
from binance import binance

from .auth import binance_auth
from .logger import get_logger, get_decorator
from .mysql import Mysql
from .redis_conn import Redis
from .balance import Balance
from .balance_common import get_base, get_step_precision
from .common import perc_diff, add_perc, sub_perc
from .alerts import send_gmail_alert, send_push_notif, send_slack_message
from . import config
GET_EXCEPTIONS = get_decorator((Exception))

class Trade():
    """Buy & Sell class"""

    def __init__(self, interval=None, test_data=False, test_trade=False):
        self.logger = get_logger(__name__)
        self.test_data = test_data
        self.test_trade = test_trade
        self.max_trades = int(config.main.max_trades)
        self.divisor = int(config.main.divisor) if config.main.divisor else None
        account = config.accounts.binance[0]
        binance_auth(account)

        self.interval = interval

    @staticmethod
    @GET_EXCEPTIONS
    def get_open_price(pair=None):
        """ return lowest buying request """
        return sorted([float(item) for item in binance.depth(pair)["asks"].keys()])[0]

    @staticmethod
    @GET_EXCEPTIONS
    def get_close_price(pair=None):
        """ return highest selling price """
        return sorted([float(item) for item in binance.depth(pair)["bids"].keys()])[-1]

    def send_redis_trade(self, pair, price, interval, event):
        """
        Send trade event to redis
        """
        self.logger.debug('Strategy - Adding to redis')

        # get last close time
        redis = Redis()
        close_time = redis.get_items(pair, interval)[-1].decode().split(':')[-1]
        data = {"event":{"result": event,
                         "current_price": format(float(price), ".20f"),
                         "date": close_time,
                        }}

        redis.redis_conn(pair, interval, data, close_time)
        del redis

    @GET_EXCEPTIONS
    def get_precision(self, item, amount):
        """
        Round amount to required precision
        binance uses 1 dp under given precision
        """

        precision = int(binance.exchange_info()[item]['quoteAssetPrecision']) - 1
        amt_str = format(float(amount), '.{}f'.format(precision))
        self.logger.debug("Final amount: %s" % amt_str)
        return amt_str

    def open_trade(self, items_list):
        """
        Main open trade method
        Will choose between spot/margin and long/short
        """
        if config.main.trade_type == "spot" and config.main.trade_direction == "long":
            self.open_spot_long(items_list)
        elif config.main.trade_type == "margin" and config.main.trade_direction == "short":
            self.open_margin_short(items_list)

    def close_trade(self, items_list, name=None, drawdowns={}, drawups={}):
        """
        Main close trade method
        Will choose between spot/margin and long/short
        """

        if config.main.trade_type == "spot" and  config.main.trade_direction == "long":
            self.close_spot_long(items_list, name, drawdowns, drawups)
        elif config.main.trade_type == "margin" and  config.main.trade_direction == "short":
            self.close_margin_short(items_list, name, drawdowns)

    def open_margin_long(self, buy_list):
        """
        Buy as many items as we can from buy_list depending on max amount of trades, and current
        balance in base currency
        """
        self.logger.info("We have %s potential items to buy" % len(buy_list))

        drain = str2bool(config.main.drain)
        prod = str2bool(config.main.production)
        if drain and not self.test_data:
            self.logger.warning("Skipping Buy as %s is in drain" % self.interval)
            return

        if buy_list:
            dbase = Mysql(test=self.test_data, interval=self.interval)
            if self.test_data or self.test_trade:
                self.logger.error("Unable to perform margin long trade in test mode, use spot")
                return
            else:
                balance = Balance(test=False)
                prices = balance.get_balance()

            for item, current_time, current_price in buy_list:
                base = get_base(item)
                try:
                    last_open_price = dbase.fetch_sql_data("select base_in from trades where "
                                                           "pair='{0}'".format(item),
                                                           header=False)[-1][-1]
                    last_open_price = float(last_open_price) if last_open_price else 0
                except IndexError:
                    last_open_price = 0
                try:
                    current_base_bal = prices['margin'][base]['count']
                except KeyError:
                    current_base_bal = 0

                current_trades = dbase.get_trades()
                avail_slots = self.max_trades - len(current_trades)
                self.logger.info("%s buy slots available" % avail_slots)

                if dbase.get_recent_high(item, current_time, 12, 200):
                    self.logger.warning("Recently sold %s with high profit, skipping" % item)
                    break
                elif avail_slots <= 0:
                    self.logger.warning("Too many trades, skipping")
                    break

                if self.divisor:
                    proposed_base_amount = current_base_bal / self.divisor
                else:
                    proposed_base_amount = current_base_bal / (self.max_trades + 1)
                self.logger.info('item: %s, proposed: %s, last:%s'
                                 % (item, proposed_base_amount, last_open_price))
                base_amount = max(proposed_base_amount, last_open_price)
                cost = current_price
                main_pairs = config.main.pairs

                if item not in main_pairs and not self.test_data:
                    self.logger.warning("%s not in buy_list, but active trade "
                                        "exists, skipping..." % item)
                    continue
                if (base_amount >= (current_base_bal / self.max_trades) and avail_slots <= 5):
                    self.logger.info("Reducing trade value by a third")
                    base_amount /= 1.5

                amount = base_amount / float(cost)
                if float(cost)*float(amount) >= float(current_base_bal):
                    self.logger.critical("Unable to purchase %s of %s, insufficient funds:%s/%s" %
                                         (amount, item, base_amount, current_base_bal))
                    continue
                elif item in current_trades:
                    self.logger.warning("We already have a trade of %s, skipping..." % item)
                    continue
                else:
                    self.logger.info("Buying %s of %s with %s %s"
                                     % (amount, item, base_amount, base))
                    self.logger.debug("amount to buy: %s, cost: %s, amount:%s"
                                      % (base_amount, cost, amount))
                    if prod:
                        amount_to_borrow = float(base_amount) * float(config.main.multiplier)
                        amount_to_use = sub_perc(5, amount_to_borrow)  # use 95% of borrowed funds

                        amt_str = get_step_precision(item, amount_to_use)
                        self.logger.info("Will attempt to borrow %s of %s" % (amount_to_borrow,
                                                                              base))
                        borrow_result = binance.margin_borrow(base, amount_to_borrow)
                        self.logger.info(borrow_result)

                        trade_result = binance.margin_order(symbol=item, side=binance.BUY,
                                                            quantity=amt_str,
                                                            order_type=binance.MARKET)
                        if "msg" in trade_result:
                            self.logger.error(trade_result)


                    prices = []
                    fill_price = cost

                    base_amount = trade_result.get('cummulativeQuoteQty', base_amount)

                    if 'transactTime' in trade_result:
                        # Get price from exchange
                        for fill in trade_result['fills']:
                            prices.append(float(fill['price']))
                        fill_price = sum(prices) / len(prices)
                        self.logger.info("Current price %s, Fill price: %s" % (cost, fill_price))


                        # only insert into db, if:
                        # 1. we are using test_data
                        # 2. we performed a test trade which was successful - (empty dict)
                        # 3. we proformed a real trade which was successful - (transactTime in dict)
                        dbase.insert_trade(pair=item, price=cost, date=current_time,
                                           base_amount=base_amount, quote=amount,
                                           borrowed=amount_to_borrow,
                                           multiplier=config.main.multiplier,
                                           direction=config.main.trade_direction)
                        send_push_notif('BUY', item, '%.15f' % float(cost))
                        send_gmail_alert('BUY', item, '%.15f' % float(cost))
                        send_slack_message('longs', 'BUY %s %.15f' % (item, float(cost)))

                        self.send_redis_trade(item, cost, self.interval, "BUY")
            del dbase
        else:
            self.logger.info("Nothing to buy")

    @staticmethod
    @GET_EXCEPTIONS
    def get_test_balance(dbase, account=None):
        """
        Get and return test balances
        """
        prices = defaultdict(lambda: defaultdict(defaultdict))

        prices['binance']['BTC']['count'] = 0.15
        prices['binance']['ETH']['count'] = 5.84
        prices['binance']['USDT']['count'] = 1000
        prices['binance']['USDC']['count'] = 1000
        prices['binance']['BNB']['count'] = 14
        for base in ['BTC', 'ETH', 'USDT', 'BNB', 'USDC']:
            result = dbase.fetch_sql_data("select sum(base_out-base_in) from trades "
                                          "where pair like '%{0}'"
                                          .format(base), header=False)[0][0]
            result = float(result) if result else 0
            current_trade_values = dbase.fetch_sql_data("select sum(base_in) from trades "
                                                        "where pair like '%{0}' and "
                                                        "base_out is null"
                                                        .format(base), header=False)[0][0]
            current_trade_values = float(current_trade_values) if \
                    current_trade_values else 0
            prices[account][base]['count'] += result + current_trade_values
        return prices


    @GET_EXCEPTIONS
    def open_spot_long(self, buy_list):
        """
        Buy as many items as we can from buy_list depending on max amount of trades, and current
        balance in base currency
        """
        self.logger.info("We have %s potential items to buy" % len(buy_list))

        drain = str2bool(config.main.drain)
        prod = str2bool(config.main.production)
        if drain and not self.test_data:
            self.logger.warning("Skipping Buy as %s is in drain" % self.interval)
            return

        if buy_list:
            dbase = Mysql(test=self.test_data, interval=self.interval)
            if self.test_data or self.test_trade:
                prices = self.get_test_balance(dbase, account='binance')
            else:
                balance = Balance(test=False)
                prices = balance.get_balance()

            for item, current_time, current_price in buy_list:
                base = get_base(item)
                try:
                    last_open_price = dbase.fetch_sql_data("select base_in from trades where "
                                                           "pair='{0}'".format(item),
                                                           header=False)[-1][-1]
                    last_open_price = float(last_open_price) if last_open_price else 0
                except IndexError:
                    last_open_price = 0
                try:
                    current_base_bal = prices['binance'][base]['count']
                except KeyError:
                    current_base_bal = 0
                except TypeError:
                    self.logger.critical("Unable to get balance for base %s" % base)

                current_trades = dbase.get_trades()
                avail_slots = self.max_trades - len(current_trades)
                self.logger.info("%s buy slots available" % avail_slots)

                if dbase.get_recent_high(item, current_time, 12, 200):
                    self.logger.warning("Recently sold %s with high profit, skipping" % item)
                    break
                elif avail_slots <= 0:
                    self.logger.warning("Too many trades, skipping")
                    break

                if self.divisor:
                    proposed_base_amount = current_base_bal / self.divisor
                else:
                    proposed_base_amount = current_base_bal / (self.max_trades + 1)
                self.logger.info('item: %s, proposed: %s, last:%s'
                                 % (item, proposed_base_amount, last_open_price))
                base_amount = max(proposed_base_amount, last_open_price)
                cost = current_price
                main_pairs = config.main.pairs

                if item not in main_pairs and not self.test_data:
                    self.logger.warning("%s not in buy_list, but active trade "
                                        "exists, skipping..." % item)
                    continue
                if (base_amount >= (current_base_bal / self.max_trades) and avail_slots <= 5):
                    self.logger.info("Reducing trade value by a third")
                    base_amount /= 1.5

                amount = base_amount / float(cost)
                if float(cost)*float(amount) >= float(current_base_bal):
                    self.logger.critical("Unable to purchase %s of %s, insufficient funds:%s/%s" %
                                         (amount, item, base_amount, current_base_bal))
                    continue
                elif item in current_trades:
                    self.logger.warning("We already have a trade of %s, skipping..." % item)
                    continue
                else:
                    self.logger.info("Buying %s of %s with %s %s"
                                     % (amount, item, base_amount, base))
                    self.logger.debug("amount to buy: %s, cost: %s, amount:%s"
                                      % (base_amount, cost, amount))
                    if prod and not self.test_data:
                        amt_str = get_step_precision(item, amount)
                        result = binance.spot_order(symbol=item, side=binance.BUY, quantity=amt_str,
                                                    order_type=binance.MARKET, test=self.test_trade)
                        if "msg" in result:
                            self.logger.error(result)

                        try:
                            # result empty if test_trade
                            cost = result.get('fills', {})[0].get('price', cost)
                        except KeyError:
                            pass
                        base_amount = result.get('cummulativeQuoteQty', base_amount)

                        prices = []
                        if 'transactTime' in result:
                            # Get price from exchange
                            for fill in result['fills']:
                                prices.append(float(fill['price']))
                            new_cost = sum(prices) / len(prices)
                            self.logger.info("Current price %s, Fill price: %s" % (cost, new_cost))
                            cost = new_cost

                    if self.test_data or (self.test_trade and not result) or \
                            (not self.test_trade and 'transactTime' in result):
                        # only insert into db, if:
                        # 1. we are using test_data
                        # 2. we performed a test trade which was successful - (empty dict)
                        # 3. we proformed a real trade which was successful - (transactTime in dict)
                        dbase.insert_trade(pair=item, price=cost, date=current_time,
                                           base_amount=base_amount, quote=amount,
                                           direction=config.main.trade_direction)
                        send_push_notif('BUY', item, '%.15f' % float(cost))
                        send_gmail_alert('BUY', item, '%.15f' % float(cost))
                        send_slack_message('longs', 'BUY %s %.15f' % (item, float(cost)))

                        self.send_redis_trade(item, cost, self.interval, "BUY")
            del dbase
        else:
            self.logger.info("Nothing to buy")

    @GET_EXCEPTIONS
    def close_margin_short(self, short_list, name=None, drawdowns=None):
        """
        Sell items in sell_list
        """

        prod = str2bool(config.main.production)
        if short_list:
            self.logger.info("We need to close short %s" % short_list)
            dbase = Mysql(test=self.test_data, interval=self.interval)
            for item, current_time, current_price in short_list:
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
                send_slack_message('longs', 'SELL %s %.15f %s' % (item, float(price), perc_inc))

                self.logger.info("Closing %s of %s for %.15f %s"
                                 % (quantity, item, float(price), base_out))
                if prod and not self.test_data:
                    amt_str = get_step_precision(item, quantity)
                    result = binance.spot_order(symbol=item, side=binance.SELL, quantity=amt_str,
                                                order_type=binance.MARKET, test=self.test_trade)

                    if "msg" in result:
                        self.logger.error(result)

                    prices = []
                    if 'transactTime' in result:
                        # Get price from exchange
                        for fill in result['fills']:
                            prices.append(float(fill['price']))
                        new_price = sum(prices) / len(prices)
                        self.logger.info("Current price %s, Fill price: %s" % (price, new_price))


                if self.test_data or (self.test_trade and not result) or \
                        (not self.test_trade and 'transactTime' in result):
                    if name == "api":
                        name = "%"

                    dbase.update_trades(pair=item, close_time=current_time,
                                        close_price=new_price, quote=quantity,
                                        base_out=base_out, name=name, drawdown=drawdowns[item])

                    self.send_redis_trade(item, price, self.interval, "SELL")
                else:
                    self.logger.critical("Sell Failed %s:%s" % (name, item))
            del dbase
        else:
            self.logger.info("No items to sell")


    @GET_EXCEPTIONS
    def open_margin_short(self, short_list):
        """
        bla bla bla
        """
        self.logger.info("We have %s potential items to short" % len(short_list))
        drain = str2bool(config.main.drain)
        if drain and not self.test_data:
            self.logger.warning("Skipping Buy as %s is in drain" % self.interval)
            return
        if short_list:
            dbase = Mysql(test=self.test_data, interval=self.interval)

            if self.test_trade and not self.test_data:
                self.logger.error("Unable to perform margin short test without test data")
            elif self.test_data:
                prices = self.get_test_balance(dbase, account='binance')
            try:
                current_base_bal = prices['binance'][base]['count']
            except KeyError:
                current_base_bal = 0

            for item, current_time, current_price in short_list:

                try:
                    last_open_price = dbase.fetch_sql_data("select base_in from trades where "
                                                           "pair='{0}'".format(item),
                                                           header=False)[-1][-1]
                    last_open_price = float(last_open_price) if last_open_price else 0
                except IndexError:
                    last_open_price = 0

                if self.divisor:
                    proposed_quote_amount = (current_base_bal / float(binance.prices()[item])) \
                            / self.divisor
                else:
                    proposed_quote_amount = (current_base_bal / float(binance.prices()[item])) \
                            / (self.max_trades + 1)

                self.logger.info('item: %s, proposed: %s, last:%s'
                                 % (item, proposed_quote_amount, last_open_price))
                self.logger.critical("AMROX %s quote amount" % proposed_quote_amount)

                base = get_base(item)
                current_trades = dbase.get_trades()
                avail_slots = self.max_trades - len(current_trades)
                self.logger.info("%s trade slots available" % avail_slots)

                if dbase.get_recent_high(item, current_time, 12, 200):
                    self.logger.warning("Recently closed %s with high profit, skipping" % item)
                    break
                elif avail_slots <= 0:
                    self.logger.warning("Too many trades, skipping")
                    break
                cost = current_price
                main_pairs = config.main.pairs
                if item not in main_pairs and not self.test_data:
                    self.logger.warning("%s not in list, skipping..." % item)
                    continue

                amount_to_borrow = float(proposed_quote_amount) * float(config.main.multiplier)
                amount_to_use = sub_perc(5, amount_to_borrow)  # use 95% of borrowed funds

                self.logger.critical("AMROX amount_to use %s" % amount_to_use)
                amt_str = get_step_precision(item, amount_to_use)
                base_amount = float(amt_str) * float(binance.prices()[item])

                self.logger.critical("AMROX base_amount %s" % base_amount)
                dbase.insert_trade(pair=item, price=cost, date=current_time,
                                   base_amount=base_amount,
                                   quote=amt_str, borrowed=amount_to_borrow,
                                   multiplier=config.main.multiplier,
                                   direction=config.main.trade_direction)

                self.send_redis_trade(item, cost, self.interval, "BUY")

    @GET_EXCEPTIONS
    def close_spot_long(self, sell_list, name=None, drawdowns={}, drawups={}):
        """
        Sell items in sell_list
        """

        prod = str2bool(config.main.production)
        if sell_list:
            self.logger.info("We need to sell %s" % sell_list)
            dbase = Mysql(test=self.test_data, interval=self.interval)
            for item, current_time, current_price in sell_list:
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
                send_slack_message('longs', 'SELL %s %.15f' % (item, float(price)))

                self.logger.info("Selling %s of %s for %.15f %s"
                                 % (quantity, item, float(price), base_out))
                if prod and not self.test_data:
                    amt_str = get_step_precision(item, quantity)
                    result = binance.spot_order(symbol=item, side=binance.SELL, quantity=amt_str,
                                                order_type=binance.MARKET, test=self.test_trade)

                    self.logger.error(result)
                    if "msg" in result:
                        self.logger.error(result)

                    prices = []
                    if 'transactTime' in result:
                        # Get price from exchange
                        for fill in result['fills']:
                            prices.append(float(fill['price']))
                        new_price = sum(prices) / len(prices)
                        self.logger.info("Current price %s, Fill price: %s" % (price, new_price))


                if self.test_data or (self.test_trade and not result) or \
                        (not self.test_trade and 'transactTime' in result):
                    if name == "api":
                        name = "%"

                    dbase.update_trades(pair=item, close_time=current_time,
                                        close_price=new_price, quote=quantity,
                                        base_out=base_out, name=name, drawdown=drawdowns[item],
                                        drawup=drawups[item])

                    self.send_redis_trade(item, price, self.interval, "SELL")
                else:
                    self.logger.critical("Sell Failed %s:%s" % (name, item))
            del dbase
        else:
            self.logger.info("No items to sell")


    @GET_EXCEPTIONS
    def close_margin_long(self, sell_list, name=None, drawdowns={}):
        """
        Sell items in sell_list
        """

        prod = str2bool(config.main.production)
        if sell_list:
            self.logger.info("We need to sell %s" % sell_list)
            dbase = Mysql(test=self.test_data, interval=self.interval)
            for item, current_time, current_price in sell_list:
                quantity = dbase.get_quantity(item)
                if not quantity:
                    self.logger.critical("Unable to find quantity for %s" % item)
                    return
                price = current_price
                open_price, _, _, base_in, borrowed = dbase.get_trade_value(item)[0]
                perc_inc = perc_diff(open_price, price)
                base_out = add_perc(perc_inc, base_in)

                send_gmail_alert("SELL", item, price)
                send_push_notif('SELL', item, '%.15f' % float(price))
                send_slack_message('longs', 'SELL %s %.15f' % (item, float(price)))

                self.logger.info("Selling %s of %s for %.15f %s"
                                 % (quantity, item, float(price), base_out))
                base = get_base(item)
                if prod and not self.test_data:
                    amt_str = get_step_precision(item, quantity)
                    trade_result = binance.margin_order(symbol=item, side=binance.SELL,
                                                        quantity=amt_str,
                                                        order_type=binance.MARKET)

                    if "msg" in trade_result:
                        self.logger.error(trade_result)
                    repay_result = binance.margin_repay(base, borrowed)
                    self.logger.info(repay_result)

                    prices = []
                    fill_price = price

                if 'transactTime' in trade_result:
                    # Get price from exchange
                    for fill in trade_result['fills']:
                        prices.append(float(fill['price']))
                    fill_price = sum(prices) / len(prices)
                    self.logger.info("Current price %s, Fill price: %s" % (price, fill_price))

                    if name == "api":
                        name = "%"

                    dbase.update_trades(pair=item, close_time=current_time,
                                        close_price=fill_price, quote=quantity,
                                        base_out=base_out, name=name, drawdown=drawdowns[item])

                    self.send_redis_trade(item, price, self.interval, "SELL")
                else:
                    self.logger.critical("Sell Failed %s:%s" % (name, item))
            del dbase
        else:
            self.logger.info("No items to sell")
