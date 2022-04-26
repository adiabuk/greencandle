#!/usr/bin/env python
#pylint: disable=wrong-import-position,wrong-import-order,no-member,logging-not-lazy,import-error,broad-except

"""
Analyze available data rom redis
Look for potential buys
"""
import time
from apscheduler.schedulers.blocking import BlockingScheduler
from greencandle.lib import config
config.create_config()
from pathlib import Path
from greencandle.lib.redis_conn import Redis
from greencandle.lib.logger import get_logger, exception_catcher
from greencandle.lib.alerts import send_slack_message
from greencandle.lib.common import HOUR, get_link, arg_decorator
from binance.binance import Binance

LOGGER = get_logger(__name__)
PAIRS = config.main.pairs.split()
MAIN_INDICATORS = config.main.indicators.split()
SCHED = BlockingScheduler()
INFO = Binance().exchange_info()
GET_EXCEPTIONS = exception_catcher((Exception))

@SCHED.scheduled_job('cron', minute="5",
                     hour=HOUR[config.main.interval], second="30")
def analyse_loop():
    """
    Gather data from redis and analyze
    """

    my_file = Path('/var/run/gc-data')
    while not my_file.is_file():
        # file exists
        LOGGER.info("Waiting for data collection to complete...")
        time.sleep(30)

    redis = Redis(interval=config.main.interval, test=False)
    for pair in PAIRS:
        LOGGER.debug("Analysing pair: %s" % pair)
        try:
            result = redis.get_action(pair=pair, interval=config.main.interval)[0]

            if result == "OPEN":
                LOGGER.debug("Items to buy")
                margin = "margin" if INFO[pair]['isMarginTradingAllowed'] else "spot"
                send_slack_message("notifications", "Open: %s %s %s %s" %
                                   (get_link(pair), config.main.interval,
                                    config.main.trade_direction, margin), emoji=True)
                LOGGER.info("Trade alert: %s %s %s %s" % (pair, config.main.interval,
                                                          config.main.trade_direction,
                                                          margin))
        except Exception as err_msg:
            LOGGER.critical("Error with pair %s %s" % (pair, str(err_msg)))
    LOGGER.info("End of current loop")
    del redis

@GET_EXCEPTIONS
@SCHED.scheduled_job('interval', seconds=60)
def keepalive():
    """
    Periodically touch file for docker healthcheck
    """
    Path('/var/run/greencandle').touch()

@arg_decorator
def main():
    """
    Analyse data from redis and alert to slack if there are current buying opportunities
    Required: CONFIG_ENV var and config

    Usage: analyse_data
    """

    LOGGER.info("Starting Initial loop")
    analyse_loop()
    LOGGER.info("Finished Initial loop")
    SCHED.start()

if __name__ == "__main__":
    main()
