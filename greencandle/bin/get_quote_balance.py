#!/usr/bin/env python
#pylint: disable=no-member
"""
Report quote currencies and available trading funds
"""

import sys
from greencandle.lib.balance import Balance
from greencandle.lib.auth import binance_auth
from greencandle.lib.alerts import send_slack_message
from greencandle.lib.common import QUOTES, arg_decorator, format_usd
from greencandle.lib.balance_common import get_quote
from greencandle.lib.binance_accounts import base2quote
from greencandle.lib import config

config.create_config()

@arg_decorator
def main():
    """
    Get list of available quote balances from
    * binance spot
    * binance cross margin
    * binance isolated margin

    Format and output to slack

    Usage: get_quote_balance
    """

    balances = Balance(test=False)

    phemex = config.accounts.account2_type == 'phemex'
    bal = balances.get_balance(phemex=phemex)
    client = binance_auth()
    results = ""
    results += "Spot Account:\n"
    for quote in QUOTES:
        try:
            results += "\t{} {} {}\n".format(quote, bal['binance'][quote]['count'],
                                             format_usd(bal['binance'][quote]['USD']))

        except KeyError:  # Zero Balance
            continue

    details = client.get_cross_margin_details()
    debts = {}
    free = {}
    for item in details['userAssets']:
        debt = float(item['borrowed']) + float(item['interest'])
        if debt > 0:
            debts[item['asset']] = debt
        if float(item['free']) > 0:
            free[item['asset']] = float(item['free'])

    results += "Cross Margin Account:\n"
    results += "\tAvailable to borrow: " + format_usd(client.get_max_borrow())+"\n"
    usd_debts_total = 0
    for key, val in debts.items():
        usd_debt = val if 'USD' in key else base2quote(val, key+'USDT')
        results += "\t{} debt: {} ({})\n".format(key, "{:.5f}".format(val), format_usd(usd_debt))
        usd_debts_total += usd_debt
    if usd_debts_total > 0:
        results += "\tTotal debts: " + format_usd(usd_debts_total)+"\n"


    for key, val in free.items():
        usd_debt = val if 'USD' in key else base2quote(val, key+'USDT')
        results += "\t{} free: {} ({})\n".format(key, "{:.5f}".format(val), format_usd(usd_debt))

    results += "Isolated Margin Account:\n"
    count = 0

    for pair in bal['isolated'].keys():
        if pair != 'TOTALS':
            quote = get_quote(pair)
            max_borrow = client.get_max_borrow(asset=quote, isolated_pair=pair)
            usd = max_borrow if 'USD' in quote else base2quote(max_borrow, quote+'USDT')

            if usd > 0:
                results += "\tAvailable to borrow {}: {}\n".format(pair, format_usd(usd))
                count += 1

    if count == 0:
        results += "\tNone available"
    send_slack_message('balance', results, name=sys.argv[0].split('/')[-1])
if __name__ == "__main__":
    main()
