#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
# pylint: disable=broad-except,c-extension-no-member

"""
Get ohlc (Open, High, Low, Close) values from given cryptos
and detect trends using candlestick patterns
"""

import json
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
from lib.profit import RATE

LOGGER = getLogger(__name__)
DB = Mysql()

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
            amount_to_buy_btc = price_per_trade * RATE


            for item in buy_list:

                current_trades = DB.get_trades()
                if amount_to_buy_btc > current_btc_bal:
                    LOGGER.warning("Unable to purchase, insufficient funds")
                    break
                elif len(current_trades) >= max_trades:
                    LOGGER.warning("Too many trades, skipping")
                    break
                elif item[0] in current_trades:
                    LOGGER.warning("We already have a trade of %s, skipping...", item[0])
                    continue
                else:
                    DB.insert_trade(item[0], prices_trunk[item[0]],
                                    price_per_trade, amount_to_buy_btc, total=0)
                    #binance.order(symbol=?, side=?, quantity, orderType="MARKET, price=?, test=True
                    #TODO: buy item
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
                DB.update_trades(pair=item, sell_time=current_time, sell_price=prices_trunk[item])
        else:
            LOGGER.info("No items to sell")

    agg_data = {}
    price_per_trade = int(get_config("backend")["price_per_trade"])
    max_trades = int(get_config("backend")["max_trades"])
    interval = str(get_config("backend")["interval"])
    LOGGER.debug("Price per trade: %s", price_per_trade)
    LOGGER.debug("max trades: %s", max_trades)

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
    dataframes = get_dataframes(pairs, interval=interval)

    events = Engine(prices=prices_trunk, dataframes=dataframes, interval=interval)
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
        LOGGER.critical("AMROX25 Overall exception")

    agg_data.update(data)
    return agg_data

if __name__ == "__main__":
    main()
    LOGGER.debug("COMPLETE")
