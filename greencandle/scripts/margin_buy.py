#!/usr/bin/env python
#pylint: disable=no-member,wrong-import-position

"""
Buy and sell instantly using binance margin
"""

import sys
import binance
from greencandle.lib import config
from greencandle.lib.balance_common import get_base, get_step_precision

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
    base_amount = 3000
    account = config.accounts.binance[0]
    binance_auth(account)
    base = get_base(pair)

    if side == 'BUY':
        result = binance.margin_borrow(base, base_amount)
        print("Borrow result: {}".format(result))
        quote_amount = 100/float(binance.prices()[pair])
        precise_amount = get_step_precision(pair, quote_amount)
        result = binance.margin_order(symbol=pair, side='BUY', quantity=precise_amount,
                                      orderType=binance.MARKET)

        print("Buy result: {}".format(result))
        result = binance.margin_order(symbol=pair, side='SELL', quantity=precise_amount,
                                      orderType=binance.MARKET)
    elif side == 'SELL':
        print("Sell result: {}".format(result))
        result = binance.margin_repay(base, base_amount)

        print("Repay result: {}".format(result))
    else:
        print('Unknown side: {}'.format(side))

if __name__ == '__main__':
    main()
