#!/usr/bin/env python
#pylint: disable=no-member

"""
Buy and sell instantly using binance margin
"""

import sys
from greencandle.lib.balance_common import get_quote, get_step_precision
from greencandle.lib.common import arg_decorator
from greencandle.lib.auth import binance_auth

@arg_decorator
def main():
    """
    Script for testing margin long trades

    Usage: margin_trade <pair> <side>
    """
    if len(sys.argv) < 3:
        print(f"Usage: {sys.argv[0]} <pair> <side>")
        sys.exit(1)
    pair = sys.argv[1]
    side = sys.argv[2]
    quote_amount = 3000
    client = binance_auth()
    quote = get_quote(pair)

    if side == 'OPEN':
        result = client.margin_borrow(quote, quote_amount)
        print(f"Borrow result: {result}")
        base_amount = 100/float(client.prices()[pair])
        precise_amount = get_step_precision(pair, base_amount)
        result = client.margin_order(symbol=pair, side='BUY', quantity=precise_amount,
                                     order_type=client.market)

        print(f"Buy result: {result}")
    elif side == 'CLOSE':
        result = client.margin_order(symbol=pair, side='SELL', quantity=precise_amount,
                                     order_type=client.market)
        print(f"Sell result: {result}")
        result = client.margin_repay(quote, quote_amount)

        print(f"Repay result: {result}")
    else:
        print(f'Unknown side: {result}')

if __name__ == '__main__':
    main()
