#!/usr/bin/env python
"""
Simple script to get current price of trading pair
"""

import sys
from binance import binance

def main():
    """
    Main function
    """

    prices = binance.prices()
    if sys.argv[1] == '--help':
        print("Usage: {} <pair>".format(sys.argv[0]))
    else:
        print(prices[sys.argv[1]])

if __name__ == '__main__':
    main()
