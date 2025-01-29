#!/usr/bin/env python
#pylint:disable=no-member,unused-variable,no-name-in-module
#PYTHON_ARGCOMPLETE_OK

"""
Get ohlc (Open, High, Low, Close) values from given cryptos
and detect trends using candlestick patterns
"""

import argparse
import sys
import glob
import time
from pathlib import Path
import argcomplete

from apscheduler.schedulers.blocking import BlockingScheduler
from setproctitle import setproctitle
from greencandle.lib import config

from greencandle.lib.graph import Graph
from greencandle.lib.logger import get_logger, exception_catcher
from greencandle.lib.run import ProdRunner

config.create_config()
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
    test_str = "(test)" if args.test else "(live)"
    setproctitle(f"{config.main.base_env}-gc-backend_{interval}{test_str}")

    if not args.data:
        while glob.glob(f'/var/run/{config.main.base_env}-data-{interval}-*'):
            LOGGER.info("waiting for initial data collection to complete for %s", interval)
            time.sleep(30)


    sched = BlockingScheduler()
    runner = ProdRunner()


    @GET_EXCEPTIONS
    @sched.scheduled_job('interval', seconds=20)
    def get_price():
        LOGGER.info("starting Price check")
        runner.prod_int_check(interval, args.test)
        LOGGER.info("finished Price check")

    @GET_EXCEPTIONS
    @sched.scheduled_job('interval', minutes=30)
    def get_graph():
        if not args.graph:
            return
        for pair in config.main.pairs.split():
            pair = pair.strip()
            LOGGER.info("creating graph for %s", pair)
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
    @sched.scheduled_job('interval', seconds=int(config.main.check_interval))
    def prod_run():
        LOGGER.info("starting prod run")
        runner.prod_loop(interval, args.test, data=args.data)
        LOGGER.info("finished prod run")

    if args.data:
        LOGGER.info("starting initial prod run")
        runner.prod_initial(interval) # initial run, before scheduling begins
        LOGGER.info("finished initial prod run")

    try:
        sched.start()
    except KeyboardInterrupt:
        LOGGER.warning("\nexiting on user command...")
        sys.exit(1)

if __name__ == "__main__":
    main()
    LOGGER.debug("complete")
