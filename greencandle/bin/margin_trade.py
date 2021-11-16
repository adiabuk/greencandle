#!/usr/bin/env python
#pylint: disable=no-member,wrong-import-position

"""
Buy and sell instantly using binance margin
"""

import sys
from binance import binance
from greencandle.lib import config
from greencandle.lib.balance_common import get_quote, get_step_precision

config.create_config()
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
    account = config.accounts.binance[0]
    binance_auth(account)
    quote = get_quote(pair)

    if side == 'OPEN':
        result = binance.margin_borrow(base, quote_amount)
        print("Borrow result: {}".format(result))
        base_amount = 100/float(binance.prices()[pair])
        precise_amount = get_step_precision(pair, base_amount)
        result = binance.margin_order(symbol=pair, side='BUY', quantity=precise_amount,
                                      orderType=binance.MARKET)

        print("Buy result: {}".format(result))
    elif side == 'CLOSE':
        result = binance.margin_order(symbol=pair, side='SELL', quantity=precise_amount,
                                      orderType=binance.MARKET)
        print("Sell result: {}".format(result))
        result = binance.margin_repay(base, quote_amount)

        print("Repay result: {}".format(result))
    else:
        print('Unknown side: {}'.format(side))

if __name__ == '__main__':
    main()
