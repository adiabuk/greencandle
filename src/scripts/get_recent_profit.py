#!/usr/bin/env python
#pylint:disable=wrong-import-position

"""
Get daily trading profits from database
"""
import os
import sys

BASE_DIR = os.getcwd().split("greencandle", 1)[0] + "greencandle"
sys.path.append(BASE_DIR)

from lib.profit import get_recent_profit

def main():
    """ Get profits """

    try:
        profits = get_recent_profit(interval=sys.argv[1])
    except IndexError:
        print("Usage {0} <interval>".format(sys.argv[0]))
        sys.exit(2)

    print("total = {0}".format(profits[0]))
    for key in sorted(profits[1].keys()):
        print("%s: %s" % (key, profits[1][key]))

if __name__ == "__main__":
    main()
