#!/usr/bin/env python
#pylint: disable=no-member, wrong-import-position
# PYTHON_ARGCOMPLETE_OK
"""
Run module with test data
"""

import sys
import argparse
import argcomplete
import setproctitle

from ..lib import config
# config is required before loading other modules as it is global
config.create_config(test=True)

from ..lib.mysql import Mysql
from ..lib.logger import getLogger, get_decorator
from ..lib.run import serial_test, parallel_test

LOGGER = getLogger(__name__, config.main.logging_level)
CHUNK_SIZE = 200
GET_EXCEPTIONS = get_decorator((Exception))

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
    pairs = [args.pair] if args.pair and args.serial else config.main.pairs.split()
    parallel_interval = config.main.parallel_interval.split()[0]
    parallel_interval = args.interval if args.interval else parallel_interval
    main_indicators = config.main.indicators.split()
    serial_intervals = [args.interval]
    redis_db = {"4h":1, "2h":1, "1h":1, "30m":1, "15m":1, "5m":2, "3m":3, "1m":4}[parallel_interval]

    dbase = Mysql(test=True, interval=parallel_interval)
    dbase.delete_data()
    del dbase
    if args.serial:
        serial_test(pairs, serial_intervals, args.data_dir, main_indicators)
    else:
        parallel_test(pairs, parallel_interval, redis_db, args.data_dir, main_indicators)

if __name__ == "__main__":
    print(config)
    sys.exit()
    main()
