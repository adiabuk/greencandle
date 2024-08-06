#!/usr/bin/env python
#pylint: disable=no-member

"""
Get binance balance from API and save to DB
"""

import sys
from greencandle.lib import config
from greencandle.lib.logger import exception_catcher
from greencandle.lib.common import arg_decorator
from greencandle.lib.balance import Balance
from greencandle.lib.alerts import send_slack_message

GET_EXCEPTIONS = exception_catcher((Exception))

@GET_EXCEPTIONS
@arg_decorator
def main():
    """
    Get balance from exchange and write to DB
    Also alert to slack balance channel

    Usage: write_balance
    """

    config.create_config()
    balance = Balance(test=False)
    phemex = config.accounts.account2_type == 'phemex'
    prices = balance.get_balance(margin=True, phemex=phemex)
    balance.save_balance(prices)
    balances = balance.get_saved_balance(prices)
    bal_str = f"USD: {balances['total_USD']}, BTC: {balances['total_BTC']}"

    print(bal_str)
    send_slack_message('balance', bal_str, name=sys.argv[0].rsplit('/', maxsplit=1)[-1])

if __name__ == "__main__":
    main()
