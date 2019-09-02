#!/usr/bin/env python

import argparse
import argcomplete

from greencandle.lib import config
from greencandle.lib.graph import Graph
config.create_config(test=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--db", required=True)
    parser.add_argument("-p", "--pair", required=True)
    parser.add_argument("-i", "--interval", required=True)
    parser.add_argument("-t", "--test", action="store_true", default=False, required=False)
    parser.add_argument("-o", "--output_dir", required=True)
    argcomplete.autocomplete(parser)
    args = parser.parse_args()


    graph = Graph(test=args, pair=args.pair, db=args.db, interval=args.interval)
    graph.get_data()
    graph.create_graph(args.output_dir)

if __name__ == '__main__':
    main()
