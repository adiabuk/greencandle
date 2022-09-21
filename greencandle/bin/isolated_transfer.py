#!/usr/bin/env python

"""
Transfer assets between spot and isolated
"""

import sys
from greencandle.lib.auth import binance_auth
from greencandle.lib.common import arg_decorator
from greencandle.lib.balance_common import get_quote, get_base

@arg_decorator
def main():
    """
    Transfer assets between spot and isolated
    Usage: isolated_transfer <pair> <to_isolated|from_isolated>
    """
    client = binance_auth()
    pair = sys.argv[1]
    direction = sys.argv[2]
    quote = get_quote(pair)
    base = get_base(pair)

    for symbol in quote, base:
        print("Transferring {} {} for pair:{}".format(symbol, direction, pair))
        result = client.transfer_isolated(pair, symbol, direction)
        print("Result: {}".format(result))



if __name__ == "__main__":
    main()
