#!/usr/bin/env python
#pylint: disable=no-member,no-name-in-module
"""
Collect OHLC and strategy data for later analysis
"""
import os
import time
from pathlib import Path
import requests
from setproctitle import setproctitle
from greencandle.lib import config
from greencandle.lib.run import ProdRunner
from greencandle.lib.logger import get_logger, exception_catcher
from greencandle.lib.common import arg_decorator
from greencandle.lib.aggregate_data  import collect_agg_data
from greencandle.lib.web import decorator_timer

config.create_config()
LOGGER = get_logger(__name__)
PAIRS = config.main.pairs.split()
MAIN_INDICATORS = config.main.indicators.split()
GET_EXCEPTIONS = exception_catcher((Exception))
RUNNER = ProdRunner()

def keepalive():
    """
    Periodically touch file for docker healthcheck
    """
    Path(f'/var/local/lock/gc_get_{config.main.interval}.lock').touch()

@GET_EXCEPTIONS
@decorator_timer
def get_data():
    """
    Get-data run
    """
    LOGGER.debug("starting prod run")
    interval = config.main.interval
    RUNNER.prod_loop(interval, test=True, data=True, analyse=False)
    keepalive()
    LOGGER.debug("finished prod run")

@GET_EXCEPTIONS
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
    setproctitle(f"{config.main.base_env}-get_data-{interval}")
    LOGGER.info("starting initial prod run")
    name = config.main.name.split('-')[-1]
    Path(f'/var/run/{config.main.base_env}-data-{interval}-{name}').touch()

    local_pairs = set(config.main.pairs.split())
    while True:
        # Don't start analysing until all pairs are available
        request = requests.get(f"http://stream/{config.main.interval}/all", timeout=10)
        if not request.ok:
            LOGGER.critical("unable to fetch data from streaming server")
        data = request.json()
        remote_pairs = set(data['recent'].keys())
        if local_pairs.issubset(remote_pairs):
            # we're done
            break
        # not enough pairs,
        LOGGER.info("Waiting for more pairs to become available local:%s, remote:%s",
                    len(local_pairs), len(remote_pairs))
        time.sleep(5)

    # initial run, before scheduling begins - 6 candles
    RUNNER.prod_initial(interval, test=True, first_run=True, no_of_runs=7)
    if os.path.exists(f'/var/run/{config.main.base_env}-data-{interval}-{name}'):
        os.remove(f'/var/run/{config.main.base_env}-data-{interval}-{name}')
    LOGGER.info("finished initial prod run")

    while True:
        get_data()
        collect_agg_data(interval)

if __name__ == '__main__':
    main()
