#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
# pylint: disable=broad-except,no-member,too-many-locals,wrong-import-position,unused-variable

"""
Get ohlc (Open, High, Low, Close) values from given cryptos
and detect trends using candlestick patterns
"""

import argparse
import sys
from pathlib import Path
import argcomplete
import setproctitle

from apscheduler.schedulers.blocking import BlockingScheduler
from str2bool import str2bool
from ..lib import config
config.create_config()
from ..lib.logger import getLogger
from ..lib.run import prod_loop, prod_int_check

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

    interval = args.interval if args.interval else str(config.main.interval)
    drain = str2bool(config.main.drain)
    drain_string = "(draining)" if drain else "(active)"
    setproctitle.setproctitle("greencandle-backend_{0}{1}".format(interval, drain_string))

    LOGGER.info("Starting initial prod run")
    prod_loop(interval, args.test) # initial run, before scheduling begins
    LOGGER.info("Finished initial prod run")

    times = {"30m": "01,31",
             "1h": "01",
             "15m": "01,31,46",
             "5m": "01,06,11,16,21,26,31,36,41,46,51,56",
             "3m": "01,04,07,10,13,16,19,22,25,28,31,34,37,40,43,46,49,52,55,58",
             "2h": "01",
             "3h": "01",
             "4h": "01",
            }

    sched = BlockingScheduler()

    @sched.scheduled_job('interval', seconds=60)
    def get_price():
        LOGGER.info("Starting Price check")
        prod_int_check(interval, args.test)
        LOGGER.info("Finished Price check")

    @sched.scheduled_job('interval', seconds=60)
    def keepalive():
        Path('/var/run/greencandle').touch()

    @sched.scheduled_job('cron', minute=times[interval])
    def prod_run():
        LOGGER.info("Starting prod run")
        prod_loop(interval, args.test)
        LOGGER.info("Finished prod run")

    try:
        sched.start()
    except KeyboardInterrupt:
        LOGGER.warning("\nExiting on user command...")
        sys.exit(1)

if __name__ == "__main__":
    main()
    LOGGER.debug("COMPLETE")
