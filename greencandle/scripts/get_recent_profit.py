#!/usr/bin/env python
#pylint:disable=wrong-import-position

"""
Get daily trading profits from database
"""

import sys

from ..lib import config
config.create_config(test=sys.argv[1])
from ..lib.profit import get_recent_profit

def main():
    """ Get profits """

    try:
        profits = get_recent_profit(interval=sys.argv[1], test=sys.argv[2])
    except IndexError:
        print("Usage {0} <interval> <test>".format(sys.argv[0]))
        sys.exit(2)

    print("total = {0}".format(profits[0]))
    for key in sorted(profits[1].keys()):
        print("%s: %s" % (key, profits[1][key]))

if __name__ == "__main__":
    main()
