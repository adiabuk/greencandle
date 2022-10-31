#!/usr/bin/env python
#pylint: disable=wrong-import-position,no-member

"""
Standalone script for generating graphs from data in redis
"""

import argparse
import argcomplete

from greencandle.lib import config
config.create_config()
from greencandle.lib.graph import Graph

def main():
    """Main function"""
    parser = argparse.ArgumentParser()
    parser.add_argument("-a", "--all_pairs", action="store_true", required=False, default=False)
    parser.add_argument("-p", "--pair", required=False)
    parser.add_argument("-i", "--interval", required=False)
    parser.add_argument("-t", "--test", action="store_true", default=False, required=False)
    parser.add_argument("-o", "--output_dir", required=True)
    parser.add_argument("-m", "--thumbnails", required=False, action="store_true", default=False)
    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    volume = 'vol' in config.main.indicators
    if args.all_pairs:
        pairs = config.main.pairs.split()
        for pair in pairs:
            pair = pair.strip()
            graph = Graph(test=args.test, pair=pair, interval=args.interval, volume=volume)
            graph.get_data()
            graph.create_graph(args.output_dir)
            if args.thumbnails:
                graph.get_screenshot()
                graph.resize_screenshot()

    else:
        graph = Graph(test=args, pair=args.pair, interval=args.interval)
        graph.get_data()
        graph.create_graph(args.output_dir)
        if args.thumbnails:
            graph.get_screenshot()
            graph.resize_screenshot()

if __name__ == '__main__':
    main()
