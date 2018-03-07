#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK

"""
Estimate monthly compound profit from starting investment
"""



import sys
import argparse
import argcomplete


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--start', required=True)
    parser.add_argument('-m', '--months',required=True)
    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    total = int(args.start)
    months = int(args.months)

    for i in range(0, 31 * months):
        print(i, int(total))
        total = total+(total * 0.1)

    print(total)

if __name__ == "__main__":
    main()
