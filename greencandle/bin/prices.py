#!/usr/bin/env python
"""
Simple script to get current price of trading pair
"""

import sys
from binance.binance import Binance

def main():
    """
    Main function
    """
    client = Binance()
    prices = client.prices()
    if sys.argv[1] == '--help':
        print("Usage: {} <pair>".format(sys.argv[0]))
    else:
        print(prices[sys.argv[1]])

if __name__ == '__main__':
    main()
