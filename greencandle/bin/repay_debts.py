#!/usr/bin/env python
#pylint: disable=no-member, logging-not-lazy
"""
Look for cross balances which can be paid off
"""

from greencandle.lib.auth import binance_auth
from greencandle.lib.logger import get_logger
from greencandle.lib.common import arg_decorator

@arg_decorator
def main():
    """
    Search for assets with interest and/or loan
    and if free balance is available for that asset attempt to pay
    off as much as possible
    Run from cron periodically in given environment
    """
    logger = get_logger("repay_loan")
    client = binance_auth()
    details = client.get_cross_margin_details()

    for item in details['userAssets']:
        symbol = item['asset']
        borrowed = float(item['borrowed'])
        interest = float(item['interest'])
        free = float(item['free'])
        owed = borrowed + interest

        if owed > 0 and free > 0:
            to_pay = owed if owed <= free else free
            if to_pay == 0:
                continue
            logger.info("Attempting to pay off %s of %s" % (to_pay, symbol))
            result = client.margin_repay(symbol=symbol, asset=symbol,
                                         quantity=to_pay, isolated=False)
            logger.info("Repay result for %s: %s" % (symbol, result))

if __name__ == '__main__':
    main()
