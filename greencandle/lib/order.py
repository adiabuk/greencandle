#!/usr/bin/env python
#pylint: disable=wrong-import-position,import-error,no-member

"""
Test Buy/Sell orders
"""

from __future__ import print_function
from collections import defaultdict
import math
import binance
from str2bool import str2bool

from .auth import binance_auth
from .logger import getLogger, get_decorator
from .mysql import Mysql
from .balance import Balance
from .balance_common import get_base
from .common import perc_diff, add_perc
from .alerts import send_gmail_alert, send_push_notif
from . import config
GET_EXCEPTIONS = get_decorator((Exception))

class Trade():
    """Buy & Sell class"""

    def __init__(self, interval=None, test_data=False, test_trade=False):
        self.logger = getLogger(__name__, config.main.logging_level)
        self.test_data = test_data
        self.test_trade = test_trade
        self.max_trades = int(config.main.max_trades)
        binance_auth()

        self.interval = interval

    @staticmethod
    @GET_EXCEPTIONS
    def get_buy_price(pair=None):
        """ return lowest buying request """
        return sorted([float(i) for i in binance.depth(pair)["asks"].keys()])[0]

    @staticmethod
    @GET_EXCEPTIONS
    def get_sell_price(pair=None):
        """ return highest selling price """
        return sorted([float(i) for i in binance.depth(pair)["bids"].keys()])[-1]

    @GET_EXCEPTIONS
    def buy(self, buy_list):
        """
        Buy as many items as we can from buy_list depending on max amount of trades, and current
        balance in base currency
        """
        self.logger.info("We have %s potential items to buy", len(buy_list))

        drain = str2bool(config.main.drain)
        if drain and not self.test_data:
            self.logger.warning("Skip ping Buy as %s is in drain", self.interval)
            return

        if buy_list:
            dbase = Mysql(test=self.test_data, interval=self.interval)
            if self.test_data or self.test_trade:
                prices = defaultdict(lambda: defaultdict(defaultdict))

                prices['binance']['BTC']['count'] = 0.00587
                prices['binance']['ETH']['count'] = 0.288578
                prices['binance']['USDT']['count'] = 60
                prices['binance']['USDC']['count'] = 60
                prices['binance']['BNB']['count'] = 2.847634
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
                    prices['binance'][base]['count'] += result + current_trade_values

            else:
                balance = Balance(test=False)
                prices = balance.get_balance()


            for item, current_time, current_price in buy_list:

                base = get_base(item)
                try:
                    last_buy_price = dbase.fetch_sql_data("select base_in from trades where "
                                                          "pair='{0}'".format(item),
                                                          header=False)[-1][-1]
                    last_buy_price = float(last_buy_price) if last_buy_price else 0
                except IndexError:
                    last_buy_price = 0
                current_base_bal = prices['binance'][base]['count']
                current_trades = dbase.get_trades()
                avail_slots = self.max_trades - len(current_trades)
                self.logger.info("%s buy slots available", avail_slots)
                if avail_slots <= 0:
                    self.logger.warning("Too many trades, skipping")
                    break
                proposed_base_amount = current_base_bal / (self.max_trades + 1)
                self.logger.info('item: %s, proposed: %s, last:%s', item, proposed_base_amount,
                                 last_buy_price)
                base_amount = max(proposed_base_amount, last_buy_price)
                cost = current_price
                main_pairs = config.main.pairs

                if item not in main_pairs and not self.test_data:
                    self.logger.warning("%s not in buy_list, but active trade "
                                        "exists, skipping...", item)
                    continue
                if (base_amount >= (current_base_bal / self.max_trades) and avail_slots <= 5):
                    self.logger.info("Reducing trade value by a third")
                    base_amount /= 1.5

                amount = base_amount / float(cost)
                if float(cost)*float(amount) >= float(current_base_bal):
                    self.logger.warning("Unable to purchase %s of %s, insufficient funds:%s/%s",
                                        amount, item, base_amount, current_base_bal)
                    continue
                elif item in current_trades:
                    self.logger.warning("We already have a trade of %s, skipping...", item)
                    continue
                else:
                    self.logger.info("Buying %s of %s with %s %s", amount, item, base_amount, base)
                    self.logger.debug("amount to buy: %s, cost: %s, amount:%s",
                                      base_amount, cost, amount)
                    if not self.test_data:
                        # Round amount to required precision
                        step_size = binance.exchange_info()[item]["stepSize"]
                        precision = int(round(-math.log(step_size, 10), 0))
                        amount = round(amount, precision)

                        result = binance.order(symbol=item, side=binance.BUY, quantity=amount,
                                               price='', orderType=binance.MARKET,
                                               test=self.test_trade)

                    if self.test_data or (self.test_trade and not result) or \
                            (not self.test_trade and 'transactTime' in result):
                        # only insert into db, if:
                        # 1. we are using test_data
                        # 2. we performed a test trade which was successful - (empty dict)
                        # 3. we proformed a real trade which was successful - (transactTime in dict)
                        dbase.insert_trade(pair=item, price=cost, date=current_time,
                                           base_amount=base_amount, quote=amount)
                        send_push_notif('BUY', item, '%f' % float(cost))
                        send_gmail_alert('BUY', item, '%f' % float(cost))
            del dbase
        else:
            self.logger.info("Nothing to buy")

    @GET_EXCEPTIONS
    def sell(self, sell_list):
        """
        Sell items in sell_list
        """

        if sell_list:
            self.logger.info("We need to sell %s", sell_list)
            dbase = Mysql(test=self.test_data, interval=self.interval)
            for item, current_time, current_price in sell_list:
                quantity = dbase.get_quantity(item)
                if not quantity:
                    self.logger.critical("Unable to find quantity for %s", item)
                    return
                price = current_price
                buy_price, _, _, base_in = dbase.get_trade_value(item)[0]
                perc_inc = perc_diff(buy_price, price)
                base_out = add_perc(perc_inc, base_in)

                send_gmail_alert("SELL", item, price)
                send_push_notif('SELL', item, price)
                if not self.test_data:
                    result = binance.order(symbol=item, side=binance.SELL, quantity=quantity,
                                           price='', orderType=binance.MARKET, test=self.test_trade)

                if self.test_data or (self.test_trade and not result) or \
                        (not self.test_trade and 'transactTime' in result):
                    dbase.update_trades(pair=item, sell_time=current_time,
                                        sell_price=price, quote=quantity, base_out=base_out)

                else:
                    self.logger.critical("Sell Failed")
            del dbase
        else:
            self.logger.info("No items to sell")
