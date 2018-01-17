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
PAIR = "XZCETH"
ASK = sorted([float(i) for i in binance.depth(PAIR)['asks'].keys()])[0]
BID = sorted([float(i) for i in binance.depth(PAIR)['bids'].keys()])[-1]

print("ask (buying price from):", ASK)
print("bid (selling price to):", BID)
