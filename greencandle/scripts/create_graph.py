#!/usr/bin/env python

import os
import argparse
import argcomplete
from greencandle.lib.graph import create_graph, get_data

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--db")
    parser.add_argument("-i", "--interval")
    parser.add_argument("-t", "--test", action="store_true", default=False)
    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    dataframes = get_data(test=args.test, db=args.db, interval=args.interval)
    create_graph('ETHBTC', dataframes)

if __name__ == '__main__':
    main()
