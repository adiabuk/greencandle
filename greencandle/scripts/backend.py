#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
# pylint: disable=broad-except,no-member,too-many-locals,wrong-import-position

"""
Get ohlc (Open, High, Low, Close) values from given cryptos
and detect trends using candlestick patterns
"""

import argparse
import time
import sys
import re
import argcomplete
import setproctitle

from str2bool import str2bool
from ..lib import config
config.create_config(test=False)
from ..lib.logger import getLogger
from ..lib.run import prod_loop

LOGGER = getLogger(__name__, config.main.logging_level)

def main():
    """ main function """
    parser = argparse.ArgumentParser()
    parser.add_argument("-g", "--graph", action="store_true", default=False)
    parser.add_argument("-j", "--json", action="store_true", default=False)
    parser.add_argument("-t", "--test", action="store_true", default=False)
    parser.add_argument("-i", "--interval")
    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    starttime = time.time()
    interval = args.interval if args.interval else str(config.main.interval)
    minutes = [int(s) for s in re.findall(r'(\d+)[mh]', interval)][0]
    drain = str2bool(config.main['drain_'+interval])
    drain_string = "(draining)" if drain else "(active)"
    setproctitle.setproctitle("greencandle-backend_{0}{1}".format(interval, drain_string))
    while True:
        try:
            prod_loop(interval, args.test)
        except KeyboardInterrupt:
            LOGGER.warning("\nExiting on user command...")
            sys.exit(1)
        remaining_time = (minutes * 60.0) - ((time.time() - starttime) % 60.0)
        LOGGER.info("Sleeping for %s seconds", remaining_time)
        time.sleep(remaining_time)


if __name__ == "__main__":
    main()
    LOGGER.debug("COMPLETE")
