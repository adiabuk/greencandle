"""common functions"""

import math
from collections import defaultdict
from binance import binance

def default_to_regular(ddict):
    """
    convert defaultdict of defaultdict to regualr nested dict using recursion
    """

    if isinstance(ddict, defaultdict):
        ddict = {k: default_to_regular(v) for k, v in ddict.items()}
    return ddict

def get_quote(pair):
    """Return Quote Currency of trading pair"""
    main = ['USDT', 'USDC', 'BTC', 'ETH', 'BNB', 'GBP']
    try:
        return list(filter(pair.endswith, main))[0]
    except IndexError:
        return None

def get_base(pair):
    """Return base Currency"""
    quote = get_quote(pair)
    return pair.replace(quote,"")

def flatten(flat):
    """
    traverse tree to find flatten-able object
    cast to list to avoid RuntimeError-dict size changed
    """
    for item_key, item_val in list(flat.items()):  # second level
        if item_key == "filters":
            for i in item_val:
                for key, val in i.items():
                    if key != "filterType" and key not in flat:
                        flat[key] = val

    del flat["filters"]
    return flat

def get_step_precision(item, amount):
    """
    Get/apply precision required for trading pair from exchange
    """
    exchange_info = binance.exchange_info()[item]
    flat = flatten(exchange_info)
    step_size = float(flat['stepSize'])
    precision = int(round(-math.log(step_size, 10), 0))
    return round(float(amount), precision)
