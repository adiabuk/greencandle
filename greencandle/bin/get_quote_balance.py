#!/usr/bin/env python
#pylint: disable=no-member
"""
Report quote currencies and available trading funds
"""

from greencandle.lib.balance import Balance
from greencandle.lib.auth import binance_auth
from greencandle.lib.alerts import send_slack_message
from greencandle.lib.common import QUOTES, arg_decorator, format_usd
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

    results += "Cross Margin Account:\n"
    results += "\tAvailable: " + format_usd(client.get_max_borrow())+"\n"

    results += "Isolated Margin Account:\n"
    count = 0
    for key, val in bal['isolated'].items():
        if key != 'TOTALS' and float(val['count']) > 0:
            results += "\t{} {} {}\n".format(quote, bal['isolated'][key]['count'],
                                             format_usd(bal['isolated'][key]['USD']))
            count += 1
    if count == 0:
        results += "\tNone available"
    send_slack_message('balance', results)

if __name__ == "__main__":
    main()
