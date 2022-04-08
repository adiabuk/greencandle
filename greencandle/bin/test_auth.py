#!/usr/bin/env python
#pylint: disable=wrong-import-order,no-member

"""
Test authentication to binance
"""

import sys
from greencandle.lib.auth import binance_auth

def main():
    """main function"""

    client = binance_auth()

    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("Test binance authentication using config creds")
        sys.exit(0)

    try:
        client.balances()
        print("Success")
    except ValueError:
        sys.exit("Auth Error")

if __name__ == '__main__':
    main()
