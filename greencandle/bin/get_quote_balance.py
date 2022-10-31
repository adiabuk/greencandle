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
from greencandle.lib.balance_common import get_quote, get_base
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
    results = get_spot_details(bal) + get_cross_margin_details(client) + \
            get_isolated_margin_details(bal, client)
    send_slack_message('balance', results, name=sys.argv[0].split('/')[-1])

def get_spot_details(bal=None):
    """
    Get spot quote amounts from db and return formatted string
    """
    results = ""
    # spot account
    results = ""
    results += "Spot Account:\n"
    for quote in QUOTES:
        try:
            results += "\t{} {} {}\n".format(quote, bal['binance'][quote]['count'],
                                             format_usd(bal['binance'][quote]['USD']))

        except KeyError:  # Zero Balance
            continue
    return results

def get_cross_margin_details(client=None):
    """
    Get cross margin quote amounts from exchange and return formatted string
    """
    results = ""
    # cross margin
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
    return results

def get_isolated_margin_details(bal=None, client=None):
    """
    Get isolated margin quote amounts from db + exchange and return formatted string
    """

    results = ""

    # isolated margin
    results += "Isolated Margin Account:\n"
    count = 0

    for pair in bal['isolated'].keys():
        pair = pair.strip()
        iso_debt_usd = 0
        if pair != 'TOTALS':
            quote = get_quote(pair)
            max_borrow = client.get_max_borrow(asset=quote, isolated_pair=pair)
            usd = max_borrow if 'USD' in quote else base2quote(max_borrow, quote+'USDT')

            if usd > 0:
                results += "\tAvailable to borrow {}: {}\n".format(pair, format_usd(usd))
                count += 1

            # Isolated debt

            assets = client.get_isolated_margin_details(pair)['assets'][0]
            base_debt = float(assets['baseAsset']['borrowed']) + \
                    float(assets['baseAsset']['interest'])
            quote_debt = float(assets['quoteAsset']['borrowed']) + \
                    float(assets['quoteAsset']['interest'])

            base_free = float(assets['baseAsset']['free'])
            quote_free = float(assets['quoteAsset']['free'])

            iso_debt_usd += base_debt if 'USD' in get_base(pair) else \
                    base2quote(base_debt, get_base(pair)+'USDT')
            iso_debt_usd += quote_debt if 'USD' in get_quote(pair) else \
                    base2quote(quote_debt, get_quote(pair)+'USDT')

            base_free_usd = base_free if 'USD' in get_base(pair) else \
                    base2quote(base_free, get_base(pair)+'USDT')
            quote_free_usd = quote_free if 'USD' in get_quote(pair) else \
                    base2quote(quote_free, get_quote(pair)+'USDT')

            if iso_debt_usd > 0:
                results += "\tTotal debts {}: {}\n".format(pair, format_usd(iso_debt_usd))

            if base_free > 0:
                results += "\t{} free: {} ({})\n".format(get_base(pair), base_free,
                                                         format_usd(base_free_usd))
            if quote_free > 0:
                results += "\t{} free: {} ({})\n".format(get_quote(pair), quote_free,
                                                         format_usd(quote_free_usd))

    if count == 0:
        results += "\tNone available"
    return results
if __name__ == "__main__":
    main()
