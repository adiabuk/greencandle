#!/usr/bin/env python
#pylint: disable=wrong-import-position,no-member,logging-not-lazy,import-error,bare-except
"""
Collect OHLC and strategy data for later analysis
"""
import os
from pathlib import Path
from greencandle.lib import config
from greencandle.lib.alerts import send_slack_message
config.create_config()
from greencandle.lib.run import ProdRunner
from greencandle.lib.logger import get_logger, exception_catcher
from greencandle.lib.common import arg_decorator

LOGGER = get_logger(__name__)
PAIRS = config.main.pairs.split()
MAIN_INDICATORS = config.main.indicators.split()
GET_EXCEPTIONS = exception_catcher((Exception))
RUNNER = ProdRunner()

def keepalive():
    """
    Periodically touch file for docker healthcheck
    """
    Path('/var/local/gc_get_{}.lock'.format(config.main.interval)).touch()

@GET_EXCEPTIONS
def get_data():
    """
    Get-data run
    """
    LOGGER.info("Starting prod run")
    interval = config.main.interval
    RUNNER.prod_loop(interval, test=True, data=True, analyse=False)
    keepalive()
    LOGGER.info("Finished prod run")

@GET_EXCEPTIONS
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
    send_slack_message('alerts', "Starting initial prod run")
    LOGGER.info("Starting initial prod run")
    name = config.main.name.split('-')[-1]
    Path('/var/run/{}-data-{}-{}'.format(config.main.base_env, interval, name)).touch()
    RUNNER.prod_initial(interval, test=True) # initial run, before scheduling begins
    if os.path.exists('/var/run/{}-data-{}-{}'.format(config.main.base_env, interval, name)):
        os.remove('/var/run/{}-data-{}-{}'.format(config.main.base_env, interval, name))
    send_slack_message('alerts', "Finished initial prod run")
    LOGGER.info("Finished initial prod run")

    while True:
        # continuous loop for smaller timeframes
        get_data()

if __name__ == '__main__':
    main()
