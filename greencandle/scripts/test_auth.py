#!/usr/bin/env python

from greencandle.lib import config
from greencandle.lib.auth import binance_auth
import binance


def main():
    config.create_config()
    binance_auth()
    try:
        binance.balances()
        print("Success")
    except ValueError:
        sys.exit("Auth Error")

if __name__ == '__main__':
    main()
