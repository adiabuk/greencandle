#!/usr/bin/env python
import sys
from binance import binance

def main():

    prices = binance.prices()
    if sys.argv[1] == '--help':
        print("Usage: {} <pair>".format(sys.argv[0]))
    else:
        print(prices[sys.argv[1]])

if __name__ == '__main__':
    main()
