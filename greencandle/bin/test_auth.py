#!/usr/bin/env python
#pylint: disable=wrong-import-order,no-member

"""
Test authentication to binance
"""

import sys
from greencandle.lib.common import arg_decorator
from greencandle.lib.auth import binance_auth

@arg_decorator
def main():
    """
    Check that authentication succeeds using current config
    """

    client = binance_auth()

    try:
        client.balances()
        print("Success")
    except ValueError:
        sys.exit("Auth Error")

if __name__ == '__main__':
    main()
