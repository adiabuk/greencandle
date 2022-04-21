#!/usr/bin/env python
#pylint: disable=wrong-import-order,wrong-import-position,no-member

"""
Sell a particular trade immediately
"""

import sys
import time
from binance.binance import Binance
from greencandle.lib.common import arg_decorator
from greencandle.lib import config
config.create_config()
from greencandle.lib.order import Trade

@arg_decorator
def main():
    """
    Close a long trade immediately
    Trade must belong to strategy in current config scope/container

    Usage: sell_now <pair> <interval> <test_trade> <test_data>
    """
    if len(sys.argv) < 4:
        print("Usage {} [pair] [interval] [test_trade] [test_data]".format(sys.argv[0]))
        sys.exit(1)

    pair = sys.argv[1]
    interval = sys.argv[2]

    test_trade = bool(len(sys.argv) > 3 and sys.argv[3] == "test")
    test_data = bool(len(sys.argv) > 3 and sys.argv[4] == "test")
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    client = Binance()
    current_price = client.prices()[pair]
    print(current_time, current_price)

    sells = []
    trade = Trade(interval=interval, test_data=test_data, test_trade=test_trade, config=config)
    sells.append((pair, current_time, current_price, "manual_sell"))
    trade.close_trade(sells, drawdowns={pair:0}, drawups={pair:0})

if __name__ == "__main__":
    main()
