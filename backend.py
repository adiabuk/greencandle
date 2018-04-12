#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
# pylint: disable=broad-except,c-extension-no-member

"""
Get ohlc (Open, High, Low, Close) values from given cryptos
and detect trends using candlestick patterns
"""

import argparse
import time
import sys
import argcomplete
import setproctitle
import binance
from lib.mysql import Mysql
from lib.binance_common import get_dataframes
from lib.engine import Engine
from lib.config import get_config
from lib.logger import getLogger
from lib.profit import RATE, get_quantity
from lib.redis_conn import Redis

LOGGER = getLogger(__name__)
PRICE_PER_TRADE = int(get_config("backend")["price_per_trade"])
MAX_TRADES = int(get_config("backend")["max_trades"])
INTERVAL = str(get_config("backend")["interval"])

def main():
    """ main function """
    setproctitle.setproctitle("greencandle-backend")
    parser = argparse.ArgumentParser()
    parser.add_argument("-g", "--graph", action="store_true", default=False)
    parser.add_argument("-j", "--json", action="store_true", default=False)
    parser.add_argument("-t", "--test", action="store_true", default=False)
    parser.add_argument("-p", "--pair")
    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    starttime = time.time()
    minutes = 4

    while True:
        try:
            loop(args)
        except KeyboardInterrupt:
            LOGGER.info("\nExiting on user command...")
            sys.exit(1)
        remaining_time = (minutes * 60.0) - ((time.time() - starttime) % 60.0)
        LOGGER.debug("Sleeping for %s seconds", remaining_time)
        time.sleep(remaining_time)

def loop(args):
    """
    Loop through collection cycle
    """


    def buy(buy_list):
        """
        Buy as many items as we can from buy_list depending on max amount of trades, and current
        balance in BTC
        """
        LOGGER.debug("We have %s potential items to buy", len(buy_list))
        if buy_list:
            current_btc_bal = events.balance["binance"]["BTC"]["count"]
            current_btc_bal = 5000   #FIXME

            amount_to_buy_btc = PRICE_PER_TRADE * RATE


            for item in buy_list:

                dbase = Mysql(test=False, interval=INTERVAL)
                current_trades = dbase.get_trades()
                if amount_to_buy_btc > current_btc_bal:
                    LOGGER.warning("Unable to purchase %s, insufficient funds", item)
                    break
                elif len(current_trades) >= MAX_TRADES:
                    LOGGER.warning("Too many trades, skipping")
                    break
                elif item in current_trades:
                    LOGGER.warning("We already have a trade of %s, skipping...", item[0])
                    continue
                else:
                    LOGGER.info("Buying item %s", item)
                    price = prices_trunk[item]
                    dbase = Mysql(test=False, interval=INTERVAL)
                    dbase.insert_trade(item, price, amount_to_buy_btc, investment, total=0)
                    quantity = get_quantity(price, investment)
                    binance.order(symbol=item, side=binance.BUY, quantity=quantity,
                                  orderType="MARKET", price=price, test=True)
                del dbase
        else:
            LOGGER.info("Nothing to buy")

    def sell(sell_list):
        """
        Sell items in sell_list
        """

        if sell_list:
            LOGGER.info("We need to sell %s", sell_list)
            for item in sell_list:
                current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
                dbase = Mysql(test=False, interval=INTERVAL)
                dbase.update_trades(pair=item, sell_time=current_time,
                                    sell_price=prices_trunk[item])
                del dbase
        else:
            LOGGER.info("No items to sell")


    LOGGER.debug("Price per trade: %s", PRICE_PER_TRADE)
    LOGGER.debug("max trades: %s", MAX_TRADES)

    LOGGER.debug("Starting new cycle")
    if args.pair:
        pairs = [args.pair]
    else:
        pairs = get_config("backend")["pairs"].split()
    prices = binance.prices()
    prices_trunk = {}
    for key, val in prices.items():
        if key in pairs:
            prices_trunk[key] = val
    dataframes = get_dataframes(pairs, interval=INTERVAL)

    events = Engine(prices=prices_trunk, dataframes=dataframes, interval=INTERVAL)
    events.get_data()
    dbase = Mysql(test=False, interval=INTERVAL)
    #dbase.insert_action_totals()
    dbase.clean_stale()
    del dbase
    redis = Redis(interval=INTERVAL, test=False, db=0)
    buys = []
    sells = []
    for pair in pairs:
        investment = 20   #FIXME
        buy_item, sell_item = redis.get_change(pair=pair, investment=investment)
        LOGGER.debug("Changed items: %s %s", buy_item, sell_item)
        if buy_item:
            LOGGER.info("Items to buy")
            buys.append(buy_item)
        if sell_item:
            LOGGER.info("Items to sell")
            sells.append(sell_item)
    sell(sells)
    buy(buys)
    del redis

if __name__ == "__main__":
    main()
    LOGGER.debug("COMPLETE")
