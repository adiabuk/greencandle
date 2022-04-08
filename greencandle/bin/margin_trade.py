#!/usr/bin/env python
#pylint: disable=no-member,wrong-import-position

"""
Buy and sell instantly using binance margin
"""

import sys
from greencandle.lib.balance_common import get_quote, get_step_precision

from greencandle.lib.auth import binance_auth

def main():
    """
    Main method
    """
    if sys.argv[1] == "--help":
        print("Usage: {} <pair> <side>".format(sys.argv[0]))
        sys.exit(0)
    if len(sys.argv) < 3:
        print("Usage: {} <pair> <side>".format(sys.argv[0]))
        sys.exit(1)
    pair = sys.argv[1]
    side = sys.argv[2]
    quote_amount = 3000
    client = binance_auth()
    quote = get_quote(pair)

    if side == 'OPEN':
        result = client.margin_borrow(quote, quote_amount)
        print("Borrow result: {}".format(result))
        base_amount = 100/float(client.prices()[pair])
        precise_amount = get_step_precision(pair, base_amount)
        result = client.margin_order(symbol=pair, side='BUY', quantity=precise_amount,
                                     order_type=client.MARKET)

        print("Buy result: {}".format(result))
    elif side == 'CLOSE':
        result = client.margin_order(symbol=pair, side='SELL', quantity=precise_amount,
                                     order_type=client.MARKET)
        print("Sell result: {}".format(result))
        result = client.margin_repay(quote, quote_amount)

        print("Repay result: {}".format(result))
    else:
        print('Unknown side: {}'.format(side))

if __name__ == '__main__':
    main()
