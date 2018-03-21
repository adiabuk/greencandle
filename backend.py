#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
#pylint: disable=no-member,consider-iterating-dictionary,global-statement,broad-except,
#pylint: disable=unused-variable,invalid-name,logging-not-lazy,logging-format-interpolation

"""
Get ohlc (Open, High, Low, Close) values from given cryptos
and detect trends using candlestick patterns
"""

import json
import argparse
import time
import sys
from concurrent.futures import ThreadPoolExecutor
import argcomplete
import setproctitle
import binance
from lib.mysql import mysql
from lib.binance_common import get_ohlcs
from lib.engine import Engine
from lib.config import get_config
from lib.logger import getLogger
from profit import RATE

logger = getLogger(__name__)
DB = mysql()

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
    minutes = 8

    while True:
        try:
            loop(args)
        except KeyboardInterrupt:
            logger.info("\nExiting on user command...")
            sys.exit(1)
        remaining_time = (minutes * 60.0) - ((time.time() - starttime) % 60.0)
        logger.debug("Sleeping for " + str(int(remaining_time)) + " seconds")
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
        logger.debug("We have {0} potential items to buy".format(len(buy_list)))
        if buy_list:
            current_btc_bal = events.balance["binance"]["BTC"]["count"]
            amount_to_buy_btc = price_per_trade * RATE


            for item in buy_list:

                current_trades = DB.get_trades()
                if amount_to_buy_btc > current_btc_bal:
                    logger.warning("Unable to purchase, insufficient funds")
                    break
                elif len(current_trades) >= max_trades:
                    logger.warning("Too many trades, skipping")
                    break
                elif item[0] in current_trades:
                    logger.warning("We already have a trade of {0}, skipping...".format(item[0]))
                    continue
                else:
                    DB.insert_trade(item[0], prices_trunk[item[0]],
                                    price_per_trade, amount_to_buy_btc)
                    #binance.order(symbol=?, side=?, quantity, orderType="MARKET, price=?, test=True
                    #TODO: buy item
        else:
            logger.info("Nothing to buy")

    def sell(sell_list):
        """
        Sell items in sell_list
        """
        if sell_list:
            logger.info("We need to sell {0}".format(sell_list))
            for item in sell_list:
                DB.update_trades(item, prices_trunk[item])
        else:
            logger.info("No items to sell")

    agg_data = {}
    price_per_trade = int(get_config("backend")["price_per_trade"])
    max_trades = int(get_config("backend")["max_trades"])
    logger.debug("Price per trade: {0}".format(price_per_trade))
    logger.debug("max trades: {0}".format(max_trades))

    logger.debug("Starting new cycle")
    if args.pair:
        pairs = [args.pair]
    else:
        pairs = [price for price in binance.prices().keys() if price != "123456" and
                 price.endswith("BTC")]
    prices = binance.prices()
    prices_trunk = {}
    for k, v in prices.items():
        if k.endswith("BTC"):
            prices_trunk[k] = v
    pairs = prices.keys()
    data = get_ohlcs(pairs, interval="15m")

    events = Engine(prices=prices_trunk, data=data, interval="15m")
    data = events.get_data()
    DB.insert_action_totals()
    DB.clean_stale()
    sell(DB.get_sell())
    buy(DB.get_buy())

    try:
        if args.json:
            print(json.dumps(events, indent=4))
        else:
            events.print_text()
    except Exception:
        logger.critical("AMROX25 Overall exception")

    agg_data.update(data)
    return agg_data

if __name__ == "__main__":
    main()
    logger.debug("COMPLETE")
