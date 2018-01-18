#!/usr/bin/env python

"""
Test Buy/Sell orders
"""

import os
import json
import binance

HOME_DIR = os.path.expanduser('~')
CONFIG = json.load(open(HOME_DIR + '/.binance'))
API_KEY = CONFIG['api_key']
API_SECRET = CONFIG['api_secret']


binance.set(API_KEY, API_SECRET)

def get_buy_price(pair="XZCETH"):
    """ return lowest buying request """
    return sorted([float(i) for i in binance.depth(pair)['asks'].keys()])[0]

def get_sell_price(pair="XZCETH"):
    """ return highest selling price """
    return sorted([float(i) for i in binance.depth(pair)['bids'].keys()])[-1]

def main():
    """ Main function """
    print("ask (buying price from):", get_buy_price())
    print("bid (selling price to):", get_sell_price())

if __name__ == "__main__":
    main()
