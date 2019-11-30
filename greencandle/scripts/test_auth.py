#!/usr/bin/env python

from greencandle.lib import config
from greencandle.lib.auth import binance_auth
import binance
import sys


def main():
    config.create_config()
    binance_auth()

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
