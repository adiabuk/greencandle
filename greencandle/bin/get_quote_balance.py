#!/usr/bin/env python
"""
Report quote currencies and available trading funds
"""

import sys
from greencandle.lib.balance import Balance
from greencandle.lib.auth import binance_auth
from greencandle.lib.alerts import send_slack_message
from babel.numbers import format_currency

def format_usd(amount):
    """
    Return formatted USD string, with dollar sign and 2dp
    """
    return str(format_currency(amount, 'USD', locale='en_US'))

def main():
    """
    Main function
    """
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("Usage: {} <pair>".format(sys.argv[0]))
        sys.exit(0)

    balances = Balance(test=False)

    bal = balances.get_balance()
    client = binance_auth()
    quotes = ['BTC', 'USDT', 'ETH']
    results = ""
    results += "Spot Account:\n"
    for quote in quotes:
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
