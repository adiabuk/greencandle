#!/usr/bin/env python

"""
Download historic data to be used for testing purposes
Save as a pandas dataframe in a pickle file

"""

import argparse
import argcomplete

from greencandle.lib import config
from greencandle.lib.binance_common import get_data

def main():
    """ Main function """

    config.create_config()
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--startdate", required=True)
    parser.add_argument("-d", "--days", required=True)
    parser.add_argument("-e", "--extra", required=False, default=1000, type=int,
                        help="number of extra klines")
    parser.add_argument("-i", "--intervals", nargs='+', required=False, default=[])
    parser.add_argument("-o", "--outputdir", required=True)
    parser.add_argument("-p", "--pairs", nargs='+', required=True, default=[])

    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    get_data(args.startdate, args.intervals, args.pairs, args.days, args.outputdir, args.extra)

if __name__ == "__main__":
    main()
