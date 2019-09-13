#!/usr/bin/env python
#pylint: disable=wrong-import-position

"""
Download historic data to be used for testing purposes
Save as a pandas dataframe in a pickle file

"""

import argparse
import argcomplete

from ..lib import config
config.create_config()
from ..lib.binance_common import get_data

def main():
    """ Main function """

    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--startdate", required=True)
    parser.add_argument("-d", "--days", required=True)
    parser.add_argument("-o", "--outputdir", required=True)
    parser.add_argument("-p", "--pairs", nargs='+', required=True, default=[])
    parser.add_argument("-i", "--intervals", nargs='+', required=False, default=[])

    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    get_data(args.startdate, args.intervals, args.pairs, args.days, args.outputdir)

if __name__ == "__main__":
    main()
