#!/usr/bin/env python
#pylint: disable=wrong-import-position

import os
import sys
import time
import binance

BASE_DIR = os.getcwd().split("greencandle", 1)[0] + "greencandle"
sys.path.append(BASE_DIR)

from lib.order import sell
from lib.auth import binance_auth

def main():
    binance_auth()
    pair = sys.argv[1]
    interval = sys.argv[2]
    test_trade = True if len(sys.argv) > 3 and sys.argv[3] == "test" else False
    current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
    current_price = binance.prices()[pair]
    print(current_time, current_price)
    sells = []
    sells.append((pair, current_time, current_price))
    sell(sells, test_data=False, test_trade=test_trade, interval=interval)


if __name__ == "__main__":
    main()
