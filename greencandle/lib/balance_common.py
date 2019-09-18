"""common functions"""

from collections import defaultdict

def default_to_regular(ddict):
    """
    convert defaultdict of defaultdict to regualr nested dict using recursion
    """

    if isinstance(ddict, defaultdict):
        ddict = {k: default_to_regular(v) for k, v in ddict.items()}
    return ddict

def get_base(pair):
    """Return BaseCurrency of trading pair"""
    bases = ['USDT', 'BTC', 'ETH', 'BNB']
    try:
        return list(filter(pair.endswith, bases))[0]
    except IndexError:
        return None
