#!/usr/bin/env python
#pylint: wrong-import-position

from greencandle.lib import config
config.create_config(test=False)
from greencandle.lib.balance import Balance

def main():
    balance = Balance(test=False)
    prices = balance.get_balance()
    balance.save_balance(prices)

if __name__ == "__main__":
    main()
