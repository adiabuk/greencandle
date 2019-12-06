#!/usr/bin/env python
#pylint: disable=wrong-import-position

import sys
import time
import binance

from greencandle.lib import config
config.create_config()
from greencandle.lib.order import Trade
from greencandle.lib.auth import binance_auth

def main():

    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("Sell a particular trade immediately")
        print("Usage {} [pair] [interval] [test_trade] [test_data]".format(sys.argv[0]))
        sys.exit(0)

    binance_auth()
    pair = sys.argv[1]
    interval = sys.argv[2]

    test_trade = bool(len(sys.argv) > 3 and sys.argv[3] == "test")
    test_data = bool(len(sys.argv) > 3 and sys.argv[4] == "test")
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    current_price = binance.prices()[pair]
    print(current_time, current_price)

    sells = []
    trade = Trade(interval=interval, test_data=test_data, test_trade=test_trade)
    sells.append((pair, current_time, current_price))
    trade.sell(sells)

if __name__ == "__main__":
    main()
