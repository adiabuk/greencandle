#!/usr/bin/env python
#pylint: disable=wrong-import-position,no-member,logging-not-lazy,import-error,bare-except
"""
Collect OHLC and strategy data for later analysis
"""
import os
from pathlib import Path
from binance.binance import Binance
from apscheduler.schedulers.blocking import BlockingScheduler
from greencandle.lib import config
config.create_config()
from greencandle.lib.redis_conn import Redis
from greencandle.lib.engine import Engine
from greencandle.lib.alerts import send_slack_message
from greencandle.lib.run import prod_initial
from greencandle.lib.binance_common import get_dataframes
from greencandle.lib.logger import get_logger, exception_catcher
from greencandle.lib.common import HOUR, MINUTE, arg_decorator

LOGGER = get_logger(__name__)
PAIRS = config.main.pairs.split()
MAIN_INDICATORS = config.main.indicators.split()
SCHED = BlockingScheduler()
GET_EXCEPTIONS = exception_catcher((Exception))

def test_loop(interval=None, prices=None):
    """
    Test loop
    """
    LOGGER.debug("Performaing prod loop")
    LOGGER.debug("Pairs in config: %s" % PAIRS)
    LOGGER.debug("Total unique pairs: %s" % len(PAIRS))

    LOGGER.info("Starting new cycle")
    LOGGER.debug("max trades: %s" % config.main.max_trades)

    prices_trunk = {}

    for key, val in prices.items():
        if key in PAIRS:
            prices_trunk[key] = val
    LOGGER.debug("Getting dataframes for all pairs")
    dataframes = get_dataframes(PAIRS, interval=interval, max_workers=1)
    LOGGER.debug("Done getting dataframes")

    redis = Redis(interval=interval, test=False)
    engine = Engine(prices=prices_trunk, dataframes=dataframes, interval=interval, redis=redis)
    engine.get_data(localconfig=MAIN_INDICATORS, first_run=False)
    dataframes = get_dataframes(PAIRS, interval=interval, no_of_klines=1)


@GET_EXCEPTIONS
@SCHED.scheduled_job('interval', seconds=60)
def keepalive():
    """
    Periodically touch file for docker healthcheck
    """
    Path('/var/run/greencandle').touch()

@SCHED.scheduled_job('cron', minute=MINUTE[config.main.interval],
                     hour=HOUR[config.main.interval], second="30")
def prod_run():
    """
    Prod run
    """
    interval = config.main.interval
    LOGGER.info("Starting prod run")
    if os.path.exists('/var/run/gc-data-{}'.format(config.main.interval)):
        os.remove('/var/run/gc-data-{}'.format(config.main.interval))
    client = Binance()
    prices = client.prices()
    test_loop(interval=interval, prices=prices)
    Path('/var/run/gc-data-{}'.format(config.main.interval)).touch()
    send_slack_message("notifications", "-"*100)
    LOGGER.info("Finished prod run")

@arg_decorator
def main():
    """
    Collect data:
    * OHLCs
    * Indicators

    This is stored on redis, and analysed by other services later.
    This service runs in a loop and executes periodically depending on timeframe used

    Usage: get_data
    """

    interval = config.main.interval
    LOGGER.info("Starting initial prod run")
    if os.path.exists('/var/run/gc-data-{}'.format(config.main.interval)):
        os.remove('/var/run/gc-data-{}'.format(config.main.interval))
    prod_initial(interval) # initial run, before scheduling begins
    Path('/var/run/gc-data-{}'.format(config.main.interval)).touch()
    LOGGER.info("Finished initial prod run")
    prod_run()

    SCHED.start()

if __name__ == '__main__':
    main()
