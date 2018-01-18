#!/usr/bin/env python
"""
Print Support and resistance for given traiding pair
"""

import binance
from klines import make_float
from lib.supres import supres
from lib.binance_common import get_binance_klines

def main():
    """Main function"""

    dataframe = get_binance_klines("XRPETH", interval="5m")
    close_values = make_float(dataframe.close)
    support, resistance = supres(close_values, 10)
    print("resistance:", resistance)
    print("current:", binance.prices()["XRPETH"])
    print("support:", support)

if __name__ == '__main__':
    main()
