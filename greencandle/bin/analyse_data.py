#!/usr/bin/env python
#pylint: disable=wrong-import-position,wrong-import-order,no-member,logging-not-lazy,broad-except,global-statement

"""
Analyze available data rom redis
Look for potential buys
"""
import time
import glob
import json
import sys
import requests
from str2bool import str2bool
from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler
from greencandle.lib import config
config.create_config()
from pathlib import Path
from greencandle.lib.redis_conn import Redis
from greencandle.lib.logger import get_logger, exception_catcher
from greencandle.lib.alerts import send_slack_message
from greencandle.lib.common import HOUR, MINUTE, get_tv_link, arg_decorator, convert_to_seconds
from greencandle.lib.auth import binance_auth
from concurrent.futures import ThreadPoolExecutor

LOGGER = get_logger(__name__)
PAIRS = config.main.pairs.split()
MAIN_INDICATORS = config.main.indicators.split()
SCHED = BlockingScheduler()
GET_EXCEPTIONS = exception_catcher((Exception))
TRIGGERED = {}
FORWARD = False

@SCHED.scheduled_job('cron', minute=MINUTE[config.main.interval],
                     hour=HOUR[config.main.interval],
                     second=config.main.check_interval)

def analyse_loop():
    """
    Gather data from redis and analyze
    """
    global TRIGGERED
    global FORWARD
    LOGGER.debug("Recently triggered: %s" % str(TRIGGERED))

    client = binance_auth()
    isolated = client.get_isolated_margin_pairs()
    cross = client.get_cross_margin_pairs()
    while glob.glob('/var/run/{}-data-{}-*'.format(config.main.base_env, config.main.interval)):
        LOGGER.info("Waiting for initial data collection to complete for %s" % config.main.interval)
        time.sleep(30)

    #interval = config.main.interval
    redis = Redis()
    for pair in PAIRS:

        with ThreadPoolExecutor(max_workers=100) as pool:
            pool.submit(analyse_pair, pair, redis, isolated, cross)
    LOGGER.info("End of current loop")
    del redis

def analyse_pair(pair, redis, isolated, cross):
    """
    Analysis of individual pair
    """
    pair = pair.strip()
    interval = config.main.interval
    supported = ""
    if config.main.trade_direction != "short":
        supported += "spot "

    supported += "isolated " if pair in isolated else ""
    supported += "cross " if pair in cross else ""

    if not supported.strip():
        # don't analyse pair if spot/isolated/cross not supported
        return

    LOGGER.debug("Analysing pair: %s" % pair)
    try:
        result, _, _, current_price, _ = redis.get_action(pair=pair, interval=interval)

        if result == "OPEN":
            LOGGER.debug("Items to buy")
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S") + " UTC"

            # Only alert on a given pair once per hour
            # for each strategy
            if pair in TRIGGERED:
                diff = now - TRIGGERED[pair]
                diff_in_hours = diff.total_seconds() / 3600
                if str2bool(config.main.wait_between_trades) and diff.total_seconds() < \
                        convert_to_seconds(config.main.time_between_trades):
                    LOGGER.debug("Skipping notification for %s %s as recently triggered"
                                 % (pair, interval))
                    return
                LOGGER.debug("Triggering alert: last alert %s hours ago" % diff_in_hours)

            TRIGGERED[pair] = now
            send_slack_message("notifications", "Open: %s %s %s (%s) - %s Current: %s" %
                               (get_tv_link(pair, interval), interval,
                                config.main.trade_direction, supported.strip(), current_time,
                                current_price), emoji=True,
                               icon=':{0}-{1}:'.format(interval, config.main.trade_direction))
            if FORWARD:
                url = "http://router:1080/forward"
                env, host, strategy = config.web.forward.split(',')
                action = 1 if config.main.trade_direction == "long" else -1
                payload = {"pair": pair,
                           "text": "forwarding trade from {}".format(config.main.name),
                           "action": str(action),
                           "host": host,
                           "env": env,
                           "price": current_price,
                           "strategy": strategy}

                for _ in range(0, 3):
                    while True:
                        try:
                            requests.post(url, json.dumps(payload), timeout=10,
                                          headers={'Content-Type': 'application/json'})
                        except requests.exceptions.RequestException:
                            continue
                        break

            LOGGER.info("Trade alert: %s %s %s (%s)" % (pair, interval,
                                                        config.main.trade_direction,
                                                        supported.strip()))
    except Exception as err_msg:
        LOGGER.critical("Error with pair %s %s" % (pair, str(err_msg)))


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
    global FORWARD
    if len(sys.argv) > 1 and sys.argv[1] == "forward":
        FORWARD = True
    LOGGER.info("Starting Initial loop")
    analyse_loop()
    LOGGER.info("Finished Initial loop")
    SCHED.start()

if __name__ == "__main__":
    main()
