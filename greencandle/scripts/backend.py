#!/usr/bin/env python
# PYTHON_ARGCOMPLETE_OK
# pylint: disable=no-member, wrong-import-position, unused-variable

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

from ..lib.logger import get_logger
from ..lib.run import prod_loop, prod_int_check, prod_initial

LOGGER = get_logger(__name__)

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
    prod_initial(interval) # initial run, before scheduling begins
    LOGGER.info("Finished initial prod run")
    prod_run()

    minute = {"3m": "0,3,6,9,12,15,18,21,24,27,30,33,36,39,42,45,48,51,54,57",
              "5m": "0,5,10,15,20,25,30,35,40,45,50,55",
              "15m": "0,15,30,45",
              "30m": "0,30",
              "1h": "0",
              "2h": "0",
              "3h": "0",
              "4h": "0",
             }

    hour = {"3m": "*",
            "5m": "*",
            "15m": "*",
            "30m": "*",
            "1h": "*",
            "2h": "0,2,4,6,8,10,12,14,16,18,20,22",
            "3h": "0,3,6,9,12,15,18,21",
            "4h": "0,4,8,12,16,20"
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

    @sched.scheduled_job('cron', minute=minute[interval], hour=hour[interval], second="30")
    def prod_run():
        LOGGER.info("Starting prod run")
        prod_loop(interval, test_trade=args.test)
        LOGGER.info("Finished prod run")

    try:
        sched.start()
    except KeyboardInterrupt:
        LOGGER.warning("\nExiting on user command...")
        sys.exit(1)

if __name__ == "__main__":
    main()
    LOGGER.debug("COMPLETE")
