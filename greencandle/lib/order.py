#!/usr/bin/env python
#pylint: disable=wrong-import-position,import-error

"""
Test Buy/Sell orders
"""

from __future__ import print_function
import math
import binance
from str2bool import str2bool

from .auth import binance_auth
from .logger import getLogger, get_decorator
from .mysql import Mysql
from .balance import get_balance
from .mail import send_gmail_alert
from . import config

GET_EXCEPTIONS = get_decorator((Exception))

class Trade():

    def __init__(self, interval=None, test=False, test_data=False, test_trade=False):
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
        balance in BTC
        """
        self.logger.info("We have %s potential items to buy", len(buy_list))

        drain = str2bool(config.main['drain_' + self.interval])
        if drain and not self.test_data:
            self.logger.warning("Skipping Buy as %s is in drain", self.interval)
            return

        if buy_list:
            dbase = Mysql(test=self.test_data, interval=self.interval)
            if self.test_data or self.test_trade:
                current_btc_bal = 37000

            else:
                current_btc_bal = get_balance()['binance']['BTC']['BTC']

            for item, current_time, current_price in buy_list:

                current_trades = dbase.get_trades()
                avail_slots = self.max_trades - len(current_trades)
                self.logger.info("%s buy slots available", avail_slots)
                if avail_slots <= 0:
                    self.logger.warning("Too many trades, skipping")
                    break
                btc_amount = current_btc_bal / avail_slots

                self.logger.info("btc_amount: %s", btc_amount)
                cost = current_price
                main_pairs = config.main['pairs_'+self.interval].split()

                if item not in main_pairs:
                    self.logger.warning("%s not in buy_list, but active trade "
                                        "exists, skipping...", item)
                    continue
                if (btc_amount >= (current_btc_bal / self.max_trades) and avail_slots <= 5):
                    self.logger.info("Reducing trade value by a third")
                    btc_amount /= 1.5

                amount = math.ceil(btc_amount / float(cost))
                if (float(cost)*float(amount) >= float(current_btc_bal) or
                        float(current_btc_bal) <= 0.0031):
                    self.logger.warning("Unable to purchase %s of %s, insufficient funds:%s/%s",
                                        amount, item, btc_amount, current_btc_bal)
                    continue
                elif item in current_trades:
                    self.logger.warning("We already have a trade of %s, skipping...", item)
                    continue
                else:
                    self.logger.info("Buying %s of %s with %s BTC", amount, item, btc_amount)
                    if not self.test_data:
                        result = binance.order(symbol=item, side=binance.BUY, quantity=amount,
                                               price=btc_amount, orderType="MARKET",
                                               test=self.test_trade)
                    if self.test_data or (self.test_trade and not result) or \
                            (not self.test_trade and 'transactTime' in result):
                        # only insert into db, if:
                        # 1. we are using test_data
                        # 2. we performed a test trade which was successful - (empty dict)
                        # 3. we proformed a real trade which was successful - (transactTime in dict)
                        dbase.insert_trade(pair=item, price=cost, date=current_time,
                                           investment=20, total=amount)
                    if not self.test_data and not result:
                        send_gmail_alert("BUY", item, cost)
                    else:
                        self.logger.critical("Buy Failed")
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
                if not self.test_data:
                    result = binance.order(symbol=item, side=binance.SELL, quantity=quantity,
                                           price='', orderType="MARKET", test=self.test_trade)
                    send_gmail_alert("SELL", item, price)
                if self.test_data or (self.test_trade and not result) or \
                        (not self.test_trade and 'transactTime' in result):
                    dbase.update_trades(pair=item, sell_time=current_time, sell_price=price)
                else:
                    self.logger.critical("Sell Failed")
            del dbase
        else:
            self.logger.info("No items to sell")
