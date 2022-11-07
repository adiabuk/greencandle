#!/usr/bin/env python
#pylint: disable=wrong-import-position,no-member,logging-not-lazy,import-error,bare-except
"""
Collect OHLC and strategy data for later analysis
"""
import os
from pathlib import Path
from apscheduler.schedulers.blocking import BlockingScheduler
from greencandle.lib import config
config.create_config()
from greencandle.lib.run import prod_initial, prod_loop
from greencandle.lib.logger import get_logger, exception_catcher
from greencandle.lib.common import HOUR, MINUTE, arg_decorator

LOGGER = get_logger(__name__)
PAIRS = config.main.pairs.split()
MAIN_INDICATORS = config.main.indicators.split()
SCHED = BlockingScheduler()
GET_EXCEPTIONS = exception_catcher((Exception))

@SCHED.scheduled_job('cron', minute=MINUTE[config.main.interval],
                     hour=HOUR[config.main.interval], second=config.main.check_interval)
def prod_run():
    """
    Test loop
    """
    interval = config.main.interval
    LOGGER.info("Starting prod run")
    prod_loop(interval, test=True, data=True, analyse=False)
    LOGGER.info("Finished prod run")


@GET_EXCEPTIONS
@SCHED.scheduled_job('interval', seconds=60)
def keepalive():
    """
    Periodically touch file for docker healthcheck
    """
    Path('/var/local/greencandle').touch()

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
    if os.path.exists('/var/run/gc-data-{}'.format(interval)):
        os.remove('/var/run/gc-data-{}'.format(interval))
    prod_initial(interval, test=True) # initial run, before scheduling begins
    prod_run()
    Path('/var/run/gc-data-{}'.format(interval)).touch()
    LOGGER.info("Finished initial prod run")
    prod_run()

    SCHED.start()

if __name__ == '__main__':
    main()
