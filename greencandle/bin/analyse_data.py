#!/usr/bin/env python
#pylint: disable=wrong-import-position,wrong-import-order,no-member,logging-not-lazy,broad-except,global-statement

"""
Analyze available data rom redis
Look for potential buys
"""
import time
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from greencandle.lib import config
config.create_config()
from pathlib import Path
from greencandle.lib.redis_conn import Redis
from greencandle.lib.logger import get_logger, exception_catcher
from greencandle.lib.alerts import send_slack_message
from greencandle.lib.common import HOUR, MINUTE, get_tv_link, arg_decorator
from greencandle.lib.auth import binance_auth

LOGGER = get_logger(__name__)
PAIRS = config.main.pairs.split()
MAIN_INDICATORS = config.main.indicators.split()
SCHED = BlockingScheduler()
GET_EXCEPTIONS = exception_catcher((Exception))
TRIGGERED = {}

@SCHED.scheduled_job('cron', minute=MINUTE[config.main.interval],
                     hour=HOUR[config.main.interval], second="32")
def analyse_loop():
    """
    Gather data from redis and analyze
    """
    global TRIGGERED
    LOGGER.debug("Recently triggered: %s" % str(TRIGGERED))

    client = binance_auth()
    isolated = client.get_isolated_margin_pairs()
    cross = client.get_cross_margin_pairs()
    run_file = Path('/var/run/gc-data-{}'.format(config.main.interval))

    while not run_file.is_file():
        # file doesn't exist
        LOGGER.info("Waiting for data collection to complete...")
        time.sleep(30)
    interval = config.main.interval
    redis = Redis()
    for pair in PAIRS:
        supported = ""
        if config.main.trade_direction != "short":
            supported += "spot "

        supported += "isolated " if pair in isolated else ""
        supported += "cross " if pair in cross else ""

        if not supported.strip():
            # don't analyse pair if spot/isolated/cross not supported
            continue

        LOGGER.debug("Analysing pair: %s" % pair)
        try:
            result = redis.get_action(pair=pair, interval=interval)[0]

            if result == "OPEN":
                LOGGER.debug("Items to buy")
                now = datetime.now()
                current_time = now.strftime("%H:%M:%S") + " UTC"
                current_price = client.prices()[pair]

                # Only alert on a given pair once per hour
                # for each strategy
                if pair in TRIGGERED:
                    diff = now - TRIGGERED[pair]
                    diff_in_hours = diff.total_seconds() / 3600
                    if diff_in_hours < 1:
                        LOGGER.debug("Skipping notification for %s %s as recently triggered"
                                     % (pair, interval))
                        continue
                    LOGGER.debug("Triggering alert: last alert %s hours ago" % diff_in_hours)

                TRIGGERED[pair] = now
                send_slack_message("notifications", "Open: %s %s %s (%s) - %s Current: %s" %
                                   (get_tv_link(pair, interval), interval,
                                    config.main.trade_direction, supported.strip(), current_time,
                                    current_price), emoji=True,
                                   icon=':{0}-{1}:'.format(interval, config.main.trade_direction))

                LOGGER.info("Trade alert: %s %s %s (%s)" % (pair, interval,
                                                            config.main.trade_direction,
                                                            supported.strip()))
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
    Path('/var/local/greencandle').touch()

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
