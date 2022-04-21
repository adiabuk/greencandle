#!/usr/bin/env python
#pylint:disable=no-member,wrong-import-position,c-extension-no-member
#PYTHON_ARGCOMPLETE_OK
"""
Run module with test data
"""

import sys
import argparse
import argcomplete
import setproctitle

from ..lib import config
# config is required before loading other modules as it is global
config.create_config()

from ..lib.logger import get_logger, exception_catcher
from ..lib.run import serial_test, parallel_test

LOGGER = get_logger(__name__)
GET_EXCEPTIONS = exception_catcher((Exception))

def main():
    """
    Run test for all pairs and intervals defined in config
    """

    setproctitle.setproctitle("greencandle-test")
    parser = argparse.ArgumentParser()
    parser.add_argument("-i", "--interval")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("-s", "--serial", default=False, action="store_true")
    group.add_argument("-a", "--parallel", default=True, action="store_true")
    parser.add_argument("-d", "--data_dir", required=True)
    parser.add_argument("-p", "--pair")

    argcomplete.autocomplete(parser)
    args = parser.parse_args()
    pairs = list(args.pair.split()) if args.pair  else config.main.pairs.split()
    parallel_interval = args.interval if args.interval else config.main.interval
    main_indicators = config.main.indicators.split()
    serial_intervals = [args.interval]

    if args.serial:
        serial_test(pairs, serial_intervals, args.data_dir, main_indicators)
    else:
        parallel_test(pairs, parallel_interval, args.data_dir, main_indicators)

if __name__ == "__main__":
    sys.exit()
    main()
