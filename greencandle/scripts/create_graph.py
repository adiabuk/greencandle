#!/usr/bin/env python

import os
import sys
from greencandle.lib.graph import create_graph, get_data

def main():
    if len(sys.argv) <= 1:
        sys.exit("Usage: {0} <redis db #>".format(sys.argv[0]))

    db = sys.argv[1]
    test = True
    dataframes = get_data(test=test, db=db)
    create_graph('ETHBTC', dataframes)
    os.system('mv /tmp/simple_candlestick_ETHBTC.html /vagrant')

if __name__ == '__main__':
    main()
