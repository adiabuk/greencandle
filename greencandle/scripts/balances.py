#!/usr/bin/env python
#pylint: disable=wrong-import-position
"""
Get Current open trades, buy prices, and current price
"""

import os
import sys
import json
from collections import defaultdict
import binance

BASE_DIR = os.getcwd().split("greencandle", 1)[0] + "greencandle"
sys.path.append(BASE_DIR)


from lib.auth import binance_auth
binance_auth()

def main():
    """
    Main function
    """

    results = defaultdict(defaultdict)
    prices = binance.prices()
    for pair in prices.keys():
        data = binance.allOrders(pair)
        if all(isinstance(data, list), data, data[-1]['side'] == 'BUY'):
            results[pair]['buy'] = data[-1]['price']
            results[pair]['current'] = prices[pair]

    output = json.dumps(all, sort_keys=True,
                        indent=4, separators=(',', ': '))
    print(output)

if __name__ == "__main__":
    main()
