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

    try:
        bnb_debt = bal['margin']['BNB']['count'] if bal['margin']['BNB']['count'] < 0 else 0
        usd_debt = bnb_debt * float(client.prices()['BNBUSDT']) if bnb_debt < 0 else 0
    except KeyError:
        bnb_debt = 0
        usd_debt = 0

    results += "Cross Margin Account:\n"
    results += "\tAvailable: " + format_usd(client.get_max_borrow())+"\n"
    results += "\tBNB debt: {} {}\n".format(bnb_debt, format_usd(usd_debt))
    results += "Isolated Margin Account:\n"
    count = 0

    for pair in bal['isolated'].keys():
        if pair != 'TOTALS':
            quote = get_quote(pair)
            max_borrow = client.get_max_borrow(asset=quote, isolated_pair=pair)
            usd = max_borrow if 'USD' in quote else base2quote(max_borrow, quote+'USDT')

            if usd > 0:
                results += "\tAvailable: " + format_usd(usd)+"\n"
                count += 1

    if count == 0:
        results += "\tNone available"
    send_slack_message('balance', results, name=sys.argv[0].split('/')[-1])
if __name__ == "__main__":
    main()
