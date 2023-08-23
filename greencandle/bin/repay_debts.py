#!/usr/bin/env python
#pylint: disable=no-member,too-many-branches,too-many-locals
"""
Look for cross balances which can be paid off
"""

import sys
from greencandle.lib.auth import binance_auth
from greencandle.lib.logger import get_logger
from greencandle.lib.common import arg_decorator
from greencandle.lib.mysql import Mysql
from greencandle.lib.balance_common import get_base

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
    cross_details = client.get_cross_margin_details()
    list_only = False
    asset_filter = ''
    if len(sys.argv) > 1:
        if 'list' in sys.argv[1]:
            list_only = True
        else:
            asset_filter = sys.argv[1]

    # filter list of assets to that containing string argument
    cross_details['userAssets'] = [x for x in cross_details['userAssets']
                                   if asset_filter in x['asset']]
    dbase = Mysql()

    bases = [get_base(x[0]) for x in dbase.fetch_sql_data("select pair from open_trades",
                                                          header=False)]
    for item in cross_details['userAssets']:
        symbol = item['asset']
        borrowed = float(item['borrowed'])
        interest = float(item['interest'])
        free = float(item['free'])
        owed = borrowed + interest
        if owed > 0 and free > 0:
            to_pay = owed if owed <= free else free
            if to_pay == 0:
                continue
            if symbol in bases:
                logger.info("Skipping %s due to open trade", symbol)
            else:
                logger.info("Attempting to pay off Cross %s of %s", to_pay, symbol)
                if not list_only:
                    result = client.margin_repay(symbol=symbol, asset=symbol,
                                                 quantity=to_pay, isolated=False)
                    logger.info("Repay result for %s: %s", symbol, result)

    isolated_details = client.get_isolated_margin_details()
    for item in isolated_details['assets']:
        symbol = item['symbol']
        for side in ["quoteAsset", "baseAsset"]:
            borrowed = float(item[side]['borrowed'])
            free = float(item[side]['free'])
            asset = item[side]['asset']
            if borrowed > 0 and free > 0:
                to_pay = borrowed if borrowed < free else free
                if to_pay == 0:
                    continue
                logger.info("Attempting to pay off Isolated %s of %s %s", to_pay, asset, symbol)
                result = client.margin_repay(symbol=symbol,
                                             asset=asset,
                                             quantity=to_pay,
                                             isolated=True)
                logger.info("Repay result for %s %s: %s", symbol, asset, result)

if __name__ == '__main__':
    main()
