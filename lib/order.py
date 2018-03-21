#!/usr/bin/env python
#pylint: disable=wrong-import-position,import-error

"""
Test Buy/Sell orders
"""

from __future__ import print_function
import os
import sys

BASE_DIR = os.getcwd().split("greencandle", 1)[0] + "greencandle"
sys.path.append(BASE_DIR)


import binance
from lib.auth import binance_auth

binance_auth()

def get_buy_price(pair="XZCETH"):
    """ return lowest buying request """
    return sorted([float(i) for i in binance.depth(pair)["asks"].keys()])[0]

def get_sell_price(pair="XZCETH"):
    """ return highest selling price """
    return sorted([float(i) for i in binance.depth(pair)["bids"].keys()])[-1]

def main():
    """ Main function """
    print("ask (buying price from):", get_buy_price())
    print("bid (selling price to):", get_sell_price())

if __name__ == "__main__":
    main()
