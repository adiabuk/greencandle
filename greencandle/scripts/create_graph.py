#!/usr/bin/env python

import argparse
import argcomplete
from greencandle.lib.graph import Graph

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--db")
    parser.add_argument("-p", "--pair")
    parser.add_argument("-i", "--interval")
    parser.add_argument("-t", "--test", action="store_true", default=False)
    argcomplete.autocomplete(parser)
    args = parser.parse_args()


    graph = Graph(test=args, pair=args.pair, db=args.db, interval=args.interval)
    graph.get_data()
    graph.create_graph()

if __name__ == '__main__':
    main()
