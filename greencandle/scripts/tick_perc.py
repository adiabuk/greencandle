#!/usr/bin/env python
#pylint: disable=wrong-import-order

"""
Get percentage change for single pip
"""
import sys
import binance
from greencandle.lib import config
from greencandle.lib.common import perc_diff
config.create_config()
PAIR = sys.argv[1]

def flatten(flat):
    """
    traverse tree to find flatten-able object
    cast to list to avoid RuntimeError-dict size changed
    """

    for item_key, item_val in list(flat.items()):  # second level
        if item_key == "filters":
            for i in item_val:
                for key, val in i.items():
                    if key != "filterType" and key not in flat:
                        flat[key] = val
    del flat["filters"]
    return flat


def main():
    """ main function """
    prices = binance.prices()
    exchange_info = binance.exchange_info()[PAIR]
    flatten(exchange_info)
    price = float(prices[PAIR])
    tick_size = float(exchange_info['tickSize'])
    diff = perc_diff(price, price+tick_size)
    print(PAIR, diff)

if __name__ == '__main__':
    main()
