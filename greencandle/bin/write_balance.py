#!/usr/bin/env python
#pylint: disable=wrong-import-position,no-member

"""
Get binance balance from API and save to DB
"""

import sys
from greencandle.lib import config
config.create_config()
from greencandle.lib.common import arg_decorator
from greencandle.lib.balance import Balance
from greencandle.lib.alerts import send_slack_message

@arg_decorator
def main():
    """
    Get balance from exchange and write to DB
    Also alert to slack balance channel

    Usage: write_balance
    """

    balance = Balance(test=False)
    phemex = config.accounts.account2_type == 'phemex'
    prices = balance.get_balance(margin=True, phemex=phemex)
    balance.save_balance(prices)
    bal_str = balance.get_saved_balance(prices)

    send_slack_message('balance', bal_str, name=sys.argv[0].split('/')[-1])

if __name__ == "__main__":
    main()
