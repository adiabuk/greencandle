#!/usr/bin/env python
"""
Get Support and resistance and PIP for given traiding pair
"""

import json
import binance
from backend import make_float
from lib.supres import supres
from lib.binance_common import get_binance_klines

def pip_calc(open, close):
    if str(open).index('.') >= 3:  # JPY pair
        multiplier = 0.01
    else:
        multiplier = 0.0001

    pips = round((close - open) / multiplier)
    return int(pips)


def get_values(pair, dataframe):
    close_values = make_float(dataframe.close)
    support, resistance = supres(close_values, 10)

    try:
        value = (pip_calc(support[-1], resistance[-1]))
    except IndexError:
        print("Skipping", pair)
        return None
    data = {}
    data['value'] = value
    data['support'] = support
    data['resistance'] = resistance
    data['difference'] = float(resistance[-1]) - float(support[-1])
    return data

def main():
    """Main function"""
    data = {}
    pairs = binance.prices().keys()

    for pair in pairs:
        dataframe = get_binance_klines(pair, interval="5m")

        x = get_values(pair, dataframe)
        if x is not None:
            data[pair] = x

    # sort by pip then by difference
    sorted_prices = sorted(data.keys(), key=lambda x: (data[x]['value'], data[x]['difference']))
    print(json.dumps(sorted_prices))
    print(json.dumps(data))

if __name__ == '__main__':
    main()
