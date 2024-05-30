#!/usr/bin/env python
#pylint: disable=no-member,broad-except
"""
Flask module for manipulating API trades and displaying relevent graphs
"""
import atexit
import time
import glob
import logging
from collections import defaultdict
from flask import Flask, request, Response
from apscheduler.schedulers.background import BackgroundScheduler
from greencandle.lib import config
from greencandle.lib.common import arg_decorator
from greencandle.lib.redis_conn import Redis
from greencandle.lib.logger import get_logger

config.create_config()
LONG = set()
SHORT = set()
ALL = defaultdict(dict)
PAIRS = config.main.pairs.split()
LOGGER = get_logger(__name__)
APP = Flask(__name__, template_folder="/var/www/html", static_url_path='/',
            static_folder='/var/www/html')

@APP.route('/healthcheck', methods=["GET"])
def healthcheck():
    """
    Docker healthcheck
    Return 200
    """
    return Response(status=200)

def analyse_loop():
    """
    Gather data from redis and analyze
    """

    while glob.glob(f'/var/run/{config.main.base_env}-data-{config.main.interval}-*'):
        LOGGER.info("waiting for initial data collection to complete for %s",
                    config.main.interval)
        time.sleep(30)


    redis = Redis()
    for pair in PAIRS:
        pair = pair.strip()
        LOGGER.debug("analysing pair: %s", pair)
        try:
            result = redis.get_action(pair=pair, interval=config.main.interval)

            ALL[pair]['date'] = result[2]
            if result[4]['open'] and not result[4]['close']:
                LONG.add(pair)
                SHORT.discard(pair)
                ALL[pair]['action'] = 'open'
            elif result[4]['close'] and not result[4]['open']:
                SHORT.add(pair)
                LONG.discard(pair)
                ALL[pair]['action'] = 'close'

        except Exception as err_msg:
            LOGGER.critical("error with pair %s %s", pair, str(err_msg))
    LOGGER.info("end of current loop")
    del redis

@APP.route('/get_data', methods=["GET"])
def get_data():
    """
    Get data for all pairs including date last updated
    """
    return ALL

@APP.route('/get_trend', methods=["GET"])
def get_trend():
    """
    open/close actions for API trades
    """
    pair = request.args.get('pair')
    if pair in LONG:
        return "long"
    if pair in SHORT:
        return "short"
    if not pair:
        return {"long": list(LONG), "short": list(SHORT)}
    return "Invalid Pair"

@APP.route('/get_stoch', methods=["GET"])
def get_stoch():
    """
    Return stochastic values for given pair
    """
    pair = request.args.get('pair')
    redis = Redis()
    items = redis.get_items(pair, config.main.interval)[-2:]
    result1 = redis.get_item(items[0], 'STOCHRSI_14')
    result2 = redis.get_item(items[1], 'STOCHRSI_14')
    return (result1, result2)

@arg_decorator
def main():
    """
    API for determining entrypoint for given pair
    according to open/close rules.
    """

    scheduler = BackgroundScheduler()
    scheduler.add_job(func=analyse_loop, trigger="interval",
                      seconds=int(config.main.check_interval))
    scheduler.start()
    logging.basicConfig(level=logging.Error)
    APP.run(debug=False, host='0.0.0.0', port=6000, threaded=True)

    atexit.register(scheduler.shutdown)

if __name__ == '__main__':
    main()
