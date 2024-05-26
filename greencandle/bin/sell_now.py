#!/usr/bin/env python
#pylint: disable=no-member

"""
Sell a particular trade immediately
"""

import sys
import time
from greencandle.lib.common import arg_decorator, get_local_price
from greencandle.lib import config
from greencandle.lib.order import Trade

@arg_decorator
def main():
    """
    Close a long trade immediately
    Trade must belong to strategy in current config scope/container

    Usage: sell_now <pair> <interval> <test_trade> <test_data>
    """
    if len(sys.argv) < 4:
        print(f"Usage {sys.argv[0]} [pair] [interval] [test_trade] [test_data]")
        sys.exit(1)

    pair = sys.argv[1]
    interval = sys.argv[2]

    config.create_config()
    test_trade = bool(len(sys.argv) > 3 and sys.argv[3] == "test")
    test_data = bool(len(sys.argv) > 3 and sys.argv[4] == "test")
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    current_price = get_local_price(pair)
    print(current_time, current_price)

    sells = []
    trade = Trade(interval=interval, test_data=test_data, test_trade=test_trade, config=config)
    sells.append((pair, current_time, current_price, "manual_sell"))
    trade.close_trade(sells, drawdowns={pair:0}, drawups={pair:0})

if __name__ == "__main__":
    main()
