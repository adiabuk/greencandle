#!/usr/bin/env python

"""
Get Balance from Binance
"""

import os
import json
import pickle
import binance
import conversion

HOME_DIR = os.path.expanduser('~')
CONFIG = json.load(open(HOME_DIR + '/.binance'))
API_KEY = CONFIG['api_key']
API_SECRET = CONFIG['api_secret']
try:
    STORAGE = HOME_DIR + '/.bitcoin'
    BITCOIN = pickle.load(open(STORAGE, 'rb'))
except IOError, EOFError:
    BITCOIN={}

def add_value(key, value):
    try:
        BITCOIN[key].append(value)
    except KeyError:
        BITCOIN[key] = []
        BITCOIN[key].append(value)


binance.set(API_KEY, API_SECRET)
all = binance.balances()
PRICES = binance.prices()
TOTALS = 0

for key in all:
    if float(all[key]['free']) > 0:
        print key, all[key]['free']
        if key != 'BTC':
            bc = float(all[key]['free']) * float(PRICES[key+'BTC'])
            print bc, "BTC"
            add_value(key, bc)
            TOTALS += float(all[key]['free']) * float(PRICES[key+'BTC'])

        else:
            add_value(key, all[key]['free'])
            TOTALS += float(all[key]['free'])
            print float(all[key]['free']) * float(PRICES['BTCUSDT']), "USD"
print 'TOTAL: ', TOTALS, "BTC"
USD = TOTALS * float(PRICES['BTCUSDT'])
print "TOTAL USD: ", USD

GBP = conversion.get_exchange_rate('USD', 'GBP') * USD
add_value('USD', USD)
add_value('GBP', GBP)
pickle.dump(BITCOIN, open(STORAGE, 'wb'))

print "GBP TOTAL: ", GBP
