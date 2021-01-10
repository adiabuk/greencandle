#!/usr/bin/env python
#pylint: disable=wrong-import-order

"""
Test authentication to binance using creds in config
"""

import sys
from binance import binance

from greencandle.lib import config
from greencandle.lib.auth import binance_auth

def main():
    """main function"""

    config.create_config()
    account = config.accounts.binance[0]
    binance_auth(account)

    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("Test binance authentication using config creds")
        sys.exit(0)

    try:
        binance.balances()
        print("Success")
    except ValueError:
        sys.exit("Auth Error")

if __name__ == '__main__':
    main()
