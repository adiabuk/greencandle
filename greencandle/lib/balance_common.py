#pylint: disable=no-member
"""common functions"""

import math
from collections import defaultdict
import requests
from greencandle.lib.objects import QUOTES

def default_to_regular(ddict):
    """
    convert defaultdict of defaultdict to regualr nested dict using recursion
    """

    if isinstance(ddict, defaultdict):
        ddict = {k: default_to_regular(v) for k, v in ddict.items()}
    return ddict

def get_quote(pair):
    """Return Quote Currency of trading pair"""
    try:
        return list(filter(pair.endswith, QUOTES))[0]
    except IndexError:
        return None

def get_base(pair):
    """Return base Currency"""
    quote = get_quote(pair)
    return pair.replace(quote, "")

def get_step_precision(item, amount):
    """
    Get/apply precision required for trading pair from exchange
    """
    req = requests.get(f'http://stream/binance/exchange_info?pair={item}', timeout=20)
    step_size = float(req.json()['stepSize'])
    precision = int(round(-math.log(step_size, 10), 0))
    return round(float(amount), precision)
