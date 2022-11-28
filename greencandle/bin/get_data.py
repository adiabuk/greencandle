#!/usr/bin/env python
#pylint: disable=wrong-import-position,no-member,logging-not-lazy,import-error,bare-except
"""
Collect OHLC and strategy data for later analysis
"""
import os
import time
from pathlib import Path
from greencandle.lib import config
config.create_config()
from greencandle.lib.run import ProdRunner
from greencandle.lib.logger import get_logger, exception_catcher
from greencandle.lib.common import arg_decorator

LOGGER = get_logger(__name__)
PAIRS = config.main.pairs.split()
MAIN_INDICATORS = config.main.indicators.split()
GET_EXCEPTIONS = exception_catcher((Exception))

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
    name = config.main.name.split('-')[-1]
    Path('/var/run/{}-data-{}-{}'.format(config.main.base_env, interval, name)).touch()
    runner = ProdRunner()
    runner.prod_initial(interval, test=True) # initial run, before scheduling begins
    if os.path.exists('/var/run/{}-data-{}-{}'.format(config.main.base_env, interval, name)):
        os.remove('/var/run/{}-data-{}-{}'.format(config.main.base_env, interval, name))
    LOGGER.info("Finished initial prod run")

    while True:
        LOGGER.info("Starting prod run")
        runner.prod_loop(interval, test=True, data=True, analyse=False)
        keepalive()
        LOGGER.info("Finished prod run")
        time.sleep(int(config.main.check_interval))

if __name__ == '__main__':
    main()
