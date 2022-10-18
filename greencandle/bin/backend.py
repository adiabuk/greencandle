#!/usr/bin/env python
#pylint:disable=no-member,wrong-import-position,unused-variable,logging-not-lazy,c-extension-no-member
#PYTHON_ARGCOMPLETE_OK

"""
Get ohlc (Open, High, Low, Close) values from given cryptos
and detect trends using candlestick patterns
"""

import argparse
import sys
from pathlib import Path
import argcomplete

from apscheduler.schedulers.blocking import BlockingScheduler
import setproctitle
from greencandle.lib import config
config.create_config()

from greencandle.lib.graph import Graph
from greencandle.lib.logger import get_logger, exception_catcher
from greencandle.lib.run import prod_loop, prod_int_check, prod_initial
from greencandle.lib.common import HOUR, MINUTE
GET_EXCEPTIONS = exception_catcher((Exception))
LOGGER = get_logger(__name__)

def main():
    """ main function """

    parser = argparse.ArgumentParser()
    parser.add_argument("-g", "--graph", action="store_true", default=False)
    parser.add_argument("-j", "--json", action="store_true", default=False)
    parser.add_argument("-t", "--test", action="store_true", default=False)
    parser.add_argument("-d", "--data", action="store_true", default=False)
    parser.add_argument("-i", "--interval")
    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    interval = args.interval if args.interval else str(config.main.interval)
    test_string = "(test)" if args.test else "(live)"
    setproctitle.setproctitle("greencandle-backend_{0}{1}".format(interval, test_string))
    sched = BlockingScheduler()

    @GET_EXCEPTIONS
    @sched.scheduled_job('interval', seconds=int(config.main.check_interval))
    def get_price():
        LOGGER.info("Starting Price check")
        prod_int_check(interval, args.test)
        LOGGER.info("Finished Price check")

    @GET_EXCEPTIONS
    @sched.scheduled_job('interval', minutes=30)
    def get_graph():
        for pair in config.main.pairs.split():
            LOGGER.info("Creating graph for %s" % pair)
            volume = 'vol' in config.main.indicators
            graph = Graph(test=False, pair=pair, interval=config.main.interval,
                          volume=volume)
            graph.get_data()
            graph.create_graph('/data/graphs/')
            graph.get_screenshot()
            graph.resize_screenshot()

    @GET_EXCEPTIONS
    @sched.scheduled_job('interval', seconds=60)
    def keepalive():
        Path('/var/run/greencandle').touch()

    @GET_EXCEPTIONS
    @sched.scheduled_job('cron', minute=MINUTE[interval], hour=HOUR[interval], second="30")
    def prod_run():
        LOGGER.info("Starting prod run")
        prod_loop(interval, args.test, data=args.data)
        LOGGER.info("Finished prod run")

    if args.data:
        LOGGER.info("Starting initial prod run")
        prod_initial(interval) # initial run, before scheduling begins
        LOGGER.info("Finished initial prod run")
        prod_run()

    try:
        sched.start()
    except KeyboardInterrupt:
        LOGGER.warning("\nExiting on user command...")
        sys.exit(1)

if __name__ == "__main__":
    main()
    LOGGER.debug("COMPLETE")
