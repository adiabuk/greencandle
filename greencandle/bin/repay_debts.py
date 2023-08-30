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
from greencandle.lib.binance_accounts import get_cross_assets_with_debt, usd2gbp, base2quote

@arg_decorator
def main():
    """
    Search for assets with interest and/or loan
    and if free balance is available for that asset attempt to pay
    off as much as possible
    Run from cron periodically in given environment

    usage: repay_debts borrowed|interest [--list]
    """
    client = binance_auth()
    debt_type = sys.argv[1]
    logger = get_logger(f"repay_debts_{debt_type}")
    debt_assets = get_cross_assets_with_debt(debt_type=debt_type, amount=True)

    list_only = bool('--list' in sys.argv)

    dbase = Mysql()
    open_set = dbase.get_main_open_assets()
    prices = client.prices() if debt_type == 'interest' else None

    logger.info("%s items with debts", len(debt_assets))
    for asset, debt, free in debt_assets:

        if debt > 0 and free > 0:
            to_pay = min(debt, free)
            if to_pay <= 0:
                logger.info("Skipping %s due to insuficent funds", asset)
                continue
            if asset in open_set:
                logger.info("Skipping %s due to open trade", asset)
            else:
                logger.info("Attempting to pay off Cross %s of %s", to_pay, asset)
                if not list_only:
                    result = client.margin_repay(symbol=asset, asset=asset,
                                                 quantity=to_pay, isolated=False)
                    if debt_type == 'interest':
                        usd = to_pay if 'USD' in asset else base2quote(to_pay, asset+'USDT',
                                                                           prices=prices)
                        gbp = usd2gbp(prices) * usd
                        dbase.add_commission_payment(asset=asset,
                                                     asset_amt=to_pay,
                                                     usd_amt=usd,
                                                     gbp_amt=gbp)

                    logger.info("Repay result for %s: %s", asset, result)

if __name__ == '__main__':
    main()
