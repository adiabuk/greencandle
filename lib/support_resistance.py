#!/usr/bin/env python
#pylint: disable=wrong-import-position,import-error

"""
Get Support and resistance and PIP for given traiding pair
"""
import os
import sys

BASE_DIR = os.getcwd().split('greencandle', 1)[0] + 'greencandle'
sys.path.append(BASE_DIR)

import json
from decimal import Decimal
import numpy
import binance
from lib.supres import supres
from lib.binance_common import get_binance_klines

def pip_calc(open_val, close_val):
    open_val = Decimal(open_val)
    close_val = Decimal(close_val)
    if '.' not in str(open_val):
        multiplier = Decimal(0.0001)
    elif str(open_val).index('.') >= 3:  # JPY pair
        multiplier = Decimal(0.01)
    else:
        multiplier = Decimal(0.0001)

    pips = round((close_val - open_val) / multiplier)
    return int(pips)

def make_float(arr):
    """Convert dataframe array into float array"""
    return numpy.array([float(x) for x in arr.values])

def get_values(pair, dataframe):
    """
    return dict of
    * value
    * support - list of previous 10
    * resistance - list of previous 10
    * difference - current difference (last value)

    for given pair in dataframe
    """
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

    try:
        data['difference'] = pipify(resistance[-1]) - pipify(support[-1])
    except TypeError as type_error:
        print("Type error", support[-1], resistance[-1], type_error)
        return None
    return data

def pipify(value):
    """
    return 4 digits after decimal point
    representing the pip
    as an int
    """
    value = Decimal(value)
    try:
        pip_value = int((str(value) + "000").split('.')[-1][:4])
        return pip_value
    except ValueError:
        print("Value Error", value)
        return None

def main():
    """Main function"""
    data = {}
    pairs = binance.prices().keys()

    for pair in pairs:
        dataframe = get_binance_klines(pair, interval="15m")

        values = get_values(pair, dataframe)
        if values is not None:
            data[pair] = values

    # sort by pip then by difference
    sorted_prices = sorted(data.keys(), key=lambda x: (data[x]['value'], data[x]['difference']))
    print(json.dumps(sorted_prices))
    #print(json.dumps(data))

if __name__ == '__main__':
    main()
