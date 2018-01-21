#!/usr/bin/env python
"""
Print Support and resistance for given traiding pair
"""

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

def main():
    """Main function"""
    data = []
    pairs = binance.prices()

    prices = binance.prices()
    for pair in pairs:
        dataframe = get_binance_klines(pair, interval="5m")
        close_values = make_float(dataframe.close)
        support, resistance = supres(close_values, 10)
        #print("resistance:", resistance)
        #print("current:", binance.prices()["XRPETH"])

        #print("support:", support)
        try:
            value = (pip_calc(support[-1], resistance[-1]))
        except IndexError:
            print("Skipping", pair)
            continue
        data.append([pair, value, support, resistance])

    data.sort(key=lambda x: x[1])
    for value in data:
        print(value[0], value[1], value[2], prices[value[0]], value[3])

if __name__ == '__main__':
    main()
