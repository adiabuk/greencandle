#!/usr/bin/env python

"""
Get/Convert Balances from Binance
"""

import os
import json
import pickle
from collections import defaultdict
import binance
import conversion

HOME_DIR = os.path.expanduser('~')
CONFIG = json.load(open(HOME_DIR + '/.binance'))
API_KEY = CONFIG['api_key']
API_SECRET = CONFIG['api_secret']
try:
    STORAGE = HOME_DIR + '/.bitcoin'
    BITCOIN = pickle.load(open(STORAGE, 'rb'))
except (IOError, EOFError):
    BITCOIN = {}

def default_to_regular(ddict):
    """
    convert defaultdict of defaultdict to regualr nested dict using recursion
    """

    if isinstance(ddict, defaultdict):
        ddict = {k: default_to_regular(v) for k, v in ddict.iteritems()}
    return ddict

def add_value(key, value):
    """Add value to dict to save offline """
    try:
        BITCOIN[key].append(value)
    except KeyError:
        BITCOIN[key] = []
        BITCOIN[key].append(value)

def get_binance_values():
    """Get totals for each crypto from binance and convert to USD/GBP"""

    mydict = lambda: defaultdict(mydict)
    result = mydict()

    binance.set(API_KEY, API_SECRET)
    all_balances = binance.balances()
    prices = binance.prices()
    bitcoin_totals = 0

    for key in all_balances:
        if float(all_balances[key]['free']) > 0:  # available currency
            result["binance"][key]["count"] = all_balances[key]["free"]

            if key != 'BTC':  # currencies that need converting to BTC
                bcoin = float(all_balances[key]['free']) * float(prices[key+'BTC'])  # value in BTC
                bitcoin_totals += float(all_balances[key]['free']) * float(prices[key+'BTC'])
            else:   #btc
                bcoin = float(all_balances[key]['free'])
                bitcoin_totals += float(bcoin)

            add_value(key, bcoin)
            usd = bcoin *float(prices["BTCUSDT"])
            gbp = conversion.get_exchange_rate('USD', 'GBP') * usd
            result["binance"][key]['BTC'] = bcoin
            result["binance"][key]['USD'] = usd
            result["binance"][key]["GBP"] = gbp

    result["binance"]["TOTALS"]["BTC"] = bitcoin_totals
    usd_total = bitcoin_totals * float(prices['BTCUSDT'])
    result["binance"]["TOTALS"]["USD"] = usd_total

    gbp_total = conversion.get_exchange_rate('USD', 'GBP') * usd_total
    result["binance"]["TOTALS"]["GBP"] = gbp_total
    add_value('USD', usd_total)
    add_value('GBP', gbp_total)
    pickle.dump(BITCOIN, open(STORAGE, 'wb'))

    return default_to_regular(result)

def main():
    """print DICT of values when called directly """

    print json.dumps(get_binance_values(), indent=4)

if __name__ == "__main__":
    main()
