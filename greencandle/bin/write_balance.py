#!/usr/bin/env python
#pylint: disable=wrong-import-position,no-member

"""
Get binance balance from API and save to DB
"""

import sys
from greencandle.lib import config
config.create_config()
from greencandle.lib.balance import Balance

def main():
    """ Main Function """
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("Update database with current binance balance")
        sys.exit(0)

    balance = Balance(test=False)
    phemex = config.accounts.account2_type == 'phemex'
    prices = balance.get_balance(margin=True, phemex=phemex)
    balance.save_balance(prices)
    balance.get_saved_balance(prices)

if __name__ == "__main__":
    main()
