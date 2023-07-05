#!/usr/bin/env python
#pylint: disable=wrong-import-position,wrong-import-order,no-member,logging-not-lazy,broad-except,global-statement

"""
Analyze available data rom redis
Look for potential trades
"""
import os
import time
import glob
import json
import sys
import requests
from str2bool import str2bool
from datetime import datetime
from greencandle.lib import config
config.create_config()
from pathlib import Path
from greencandle.lib.redis_conn import Redis
from greencandle.lib.logger import get_logger, exception_catcher
from greencandle.lib.alerts import send_slack_message
from greencandle.lib.common import get_tv_link, arg_decorator, convert_to_seconds
from greencandle.lib.auth import binance_auth
from greencandle.lib.order import Trade

LOGGER = get_logger(__name__)
PAIRS = config.main.pairs.split()
MAIN_INDICATORS = config.main.indicators.split()
GET_EXCEPTIONS = exception_catcher((Exception))
TRIGGERED = {}
FORWARD = False

if sys.argv[-1] != "--help":
    CLIENT = binance_auth()
    ISOLATED = CLIENT.get_isolated_margin_pairs()
    CROSS = CLIENT.get_cross_margin_pairs()
    STORE_IN_DB = bool('STORE_IN_DB' in os.environ)

def analyse_loop():
    """
    Gather data from redis and analyze
    """
    global TRIGGERED
    global FORWARD
    LOGGER.debug("Recently triggered: %s" % str(TRIGGERED))

    Path('/var/local/greencandle').touch()
    while glob.glob('/var/run/{}-data-{}-*'.format(config.main.base_env, config.main.interval)):
        LOGGER.info("Waiting for initial data collection to complete for %s" % config.main.interval)
        time.sleep(30)

    LOGGER.debug("Start of current loop")
    redis = Redis()

    for pair in PAIRS:
        analyse_pair(pair, redis)
    LOGGER.debug("End of current loop")
    del redis

def analyse_pair(pair, redis):
    """
    Analysis of individual pair
    """
    pair = pair.strip()
    interval = config.main.interval
    supported = ""
    if config.main.trade_direction != "short":
        supported += "spot "

    supported += "isolated " if pair in ISOLATED else ""
    supported += "cross " if pair in CROSS else ""

    if not supported.strip():
        # don't analyse pair if spot/isolated/cross not supported
        return

    LOGGER.debug("Analysing pair: %s" % pair)
    try:
        result, event, current_time, current_price, match = \
                redis.get_rule_action(pair=pair, interval=interval)

        if result in ('OPEN', 'CLOSE'):
            LOGGER.debug("Trades to %s" % result.lower())
            now = datetime.now()
            items = redis.get_items(pair, interval)
            data = redis.get_item("{}:{}".format(pair, interval), items[-1]).decode()
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
            send_slack_message("notifications", "%s %s: %s %s %s (%s) - %s Data: %s" %
                               (result.lower(), str(match['{}'.format(result.lower())]),
                                get_tv_link(pair, interval), interval,
                                config.main.name, supported.strip(), current_time,
                                data), emoji=True,
                               icon=':{0}-{1}:'.format(interval, config.main.trade_direction))
            if config.main.trade_direction == 'long' and result == 'OPEN':
                action = 1
            elif config.main.trade_direction == 'short' and result == 'OPEN':
                action = -1
            else:
                action = 0


            details = [[pair, current_time, current_price, event, action]]
            trade = Trade(interval=interval, test_trade=True, test_data=False, config=config)
            if result == 'OPEN' and STORE_IN_DB:
                LOGGER.info("opening data trade for %s" % pair)
                trade.open_trade(details)
            elif result == 'CLOSE' and STORE_IN_DB:
                LOGGER.info("closing data trade for %s" % pair)
                trade.close_trade(details)

            if FORWARD:
                url = "http://router:1080/{}".format(config.web.api_token)
                env, host, strategy = config.web.forward.split(',')
                payload = {"pair": pair,
                           "text": "forwarding trade from {}".format(config.main.name),
                           "action": str(action),
                           "host": host,
                           "env": env,
                           "price": current_price,
                           "strategy": strategy}

                try:
                    requests.post(url, json.dumps(payload), timeout=10,
                                  headers={'Content-Type': 'application/json'})
                    LOGGER.info("forwarding %s %s/%s trade to: %s/%s"
                                % (pair, interval, config.main.trade_direction, env, strategy))

                except requests.exceptions.RequestException:
                    pass

            LOGGER.info("Trade alert: %s %s %s (%s)" % (pair, interval,
                                                        config.main.trade_direction,
                                                        supported.strip()))
    except Exception as err_msg:
        LOGGER.critical("Error with pair %s %s" % (pair, str(err_msg)))

@arg_decorator
def main():
    """
    Analyse data from redis and alert to slack if there are current trade opportunities
    Required: CONFIG_ENV var and config

    Usage: analyse_data
    """
    global FORWARD
    if len(sys.argv) > 1 and sys.argv[1] == "forward":
        FORWARD = True
    while True:
        analyse_loop()

if __name__ == "__main__":
    main()
