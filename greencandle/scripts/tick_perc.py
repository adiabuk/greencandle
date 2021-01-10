#!/usr/bin/env python
#pylint: disable=wrong-import-order

"""
Get percentage change for single pip
"""
import sys
from binance import binance
from greencandle.lib import config
from greencandle.lib.common import perc_diff
config.create_config()

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


    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("Get percentage change for single pip")
        sys.exit(0)
    elif len(sys.argv) !=2:
        sys.stderr.write("Usage: {} <pair>\n".format(sys.argv[0]))
        sys.exit(1)


    pair = sys.argv[1]
    prices = binance.prices()
    exchange_info = binance.exchange_info()[pair]
    flatten(exchange_info)
    price = float(prices[pair])
    tick_size = float(exchange_info['tickSize'])
    diff = perc_diff(price, price+tick_size)
    print(pair, diff)

if __name__ == '__main__':
    main()
