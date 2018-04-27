#!/usr/bin/env python
#pylint: disable=wrong-import-position,import-error

"""
Test Buy/Sell orders
"""

from __future__ import print_function
import os
import sys
import math
from str2bool import str2bool
import binance

BASE_DIR = os.getcwd().split("greencandle", 1)[0] + "greencandle"
sys.path.append(BASE_DIR)


from lib.auth import binance_auth
from lib.logger import getLogger, get_decorator
from lib.config import get_config
from lib.mysql import Mysql
from lib.balance import get_balance
from lib.mail import send_gmail_alert

LOGGER = getLogger(__name__)
MAX_TRADES = int(get_config("backend")["max_trades"])

binance_auth()
GET_EXCEPTIONS = get_decorator((Exception))

@GET_EXCEPTIONS
def get_buy_price(pair=None):
    """ return lowest buying request """
    return sorted([float(i) for i in binance.depth(pair)["asks"].keys()])[0]

@GET_EXCEPTIONS
def get_sell_price(pair=None):
    """ return highest selling price """
    return sorted([float(i) for i in binance.depth(pair)["bids"].keys()])[-1]

@GET_EXCEPTIONS
def buy(buy_list, test_data=False, test_trade=True, interval=None):
    """
    Buy as many items as we can from buy_list depending on max amount of trades, and current
    balance in BTC
    """
    LOGGER.info("We have %s potential items to buy", len(buy_list))

    drain = str2bool(get_config("backend")["drain_" + interval])
    if drain and not test_data:
        LOGGER.warning("Skipping Buy as %s is in drain", interval)
        return

    if buy_list:
        dbase = Mysql(test=test_data, interval=interval)
        if test_data:
            current_btc_bal = 0.36 # 2000GBP

        else:
            current_btc_bal = get_balance()['binance']['BTC']['BTC']

        for item, current_time, current_price in buy_list:

            current_trades = dbase.get_trades()
            avail_slots = MAX_TRADES - len(current_trades)
            LOGGER.info("%s buy slots available", avail_slots)
            if avail_slots == 0:
                LOGGER.warning("Too many trades, skipping")
                break
            btc_amount = current_btc_bal / avail_slots

            LOGGER.info("btc_amount: %s", btc_amount)
            cost = current_price

            main_pairs = get_config("backend")["pairs"].split()
            if item not in main_pairs:
                LOGGER.warning("%s not in buy_list, but active trade exists, skipping...", item)
                continue
            if (btc_amount > (current_btc_bal / MAX_TRADES) and avail_slots < 5):
                LOGGER.info("Reducing trade value by a third")
                btc_amount /= 1.5

            amount = math.ceil(btc_amount / float(cost))
            if float(btc_amount) > float(current_btc_bal) or float(current_btc_bal) < 0.0031:
                LOGGER.warning("Unable to purchase %s, insufficient funds:%s/%s",
                               item, btc_amount, current_btc_bal)
                break
            elif item in current_trades:
                LOGGER.warning("We already have a trade of %s, skipping...", item)
                continue
            else:
                LOGGER.info("Buying %s of %s with %s BTC", amount, item, btc_amount)
                if not test_data:
                    result = binance.order(symbol=item, side=binance.BUY, quantity=amount,
                                           orderType="MARKET", test=test_trade)
                if test_data or (test_trade and not result) or \
                        (not test_trade and 'transactTime' in result):
                    # only insert into db, if:
                    # 1. we are using test_data
                    # 2. we we performed a test trade which was successful - (empty dict)
                    # 3. we proformed a real trade which was successful - (transactTime in dict)
                    dbase.insert_trade(pair=item, price=cost, date=current_time,
                                       investment=20, total=amount)
                if not test_data:
                    send_gmail_alert("BUY", item, cost)
                else:
                    LOGGER.critical("Buy Failed")
        del dbase
    else:
        LOGGER.info("Nothing to buy")


@GET_EXCEPTIONS
def sell(sell_list, test_data=False, test_trade=True, interval=None):
    """
    Sell items in sell_list
    """

    if sell_list:
        LOGGER.info("We need to sell %s", sell_list)
        dbase = Mysql(test=test_data, interval=interval)
        for item, current_time, current_price in sell_list:
            quantity = dbase.get_quantity(item)
            if not quantity:
                LOGGER.critical("Unable to find quantity for %s", item)
                return
            price = current_price
            if not test_data:
                result = binance.order(symbol=item, side=binance.SELL, quantity=quantity,
                                       orderType="MARKET", test=test_trade)
            if test_data or (test_trade and not result) or \
                    (not test_trade and 'transactTime' in result):
                dbase.update_trades(pair=item, sell_time=current_time, sell_price=price)
            if not test_data:
                send_gmail_alert("SELL", item, price)

            else:
                LOGGER.critical("Sell Failed")
        del dbase
    else:
        LOGGER.info("No items to sell")

@GET_EXCEPTIONS
def main():
    """ Main function """
    print("ask (buying price from):", get_buy_price())
    print("bid (selling price to):", get_sell_price())

if __name__ == "__main__":
    main()
