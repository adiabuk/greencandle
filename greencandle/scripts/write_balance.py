#!/usr/bin/env python
#pylint: disable=wrong-import-position

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
    prices = balance.get_balance()
    balance.save_balance(prices)

if __name__ == "__main__":
    main()
