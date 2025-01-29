#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

"""
Estimate monthly compound profit from starting investment
"""

import argparse
import argcomplete

def main():
    """ Main function """
    parser = argparse.ArgumentParser()
    parser.add_argument("-s", "--start", required=True,
                        help="Initial investment")
    parser.add_argument("-m", "--months", required=True,
                        help="monber of months to calculate")
    parser.add_argument("-p", "--percent", required=True,
                        help="average percent profit per day")

    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    total = int(args.start)
    months = int(args.months)
    percent = float(args.percent)/100

    for i in range(0, 30 * months):
        print(f'{i} {int(total):,}')
        total = total+(total * percent)

if __name__ == "__main__":
    main()
