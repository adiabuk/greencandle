#!/usr/bin/env python
#pylint: disable=no-member,no-name-in-module
"""
Collect OHLC and strategy data for later analysis
"""
import os
import time
from pathlib import Path
import logging
from datetime import datetime, timedelta
from collections import defaultdict
import requests
from setproctitle import setproctitle
from flask import Flask, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from greencandle.lib import config
from greencandle.lib.run import ProdRunner
from greencandle.lib.redis_conn import Redis
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
APP = Flask(__name__, template_folder="/var/www/html", static_url_path='/',
            static_folder='/var/www/html')
DATA = defaultdict(dict)

@APP.route('/get_data', methods=["GET"])
def get_all_data():
    """
    return all data for current interval/scope
    """
    return jsonify(DATA)

@decorator_timer
def collect_data(pair):
    """
    Collect all available data for all pairs
    """
    redis = Redis()
    interval = config.main.interval
    DATA[pair]['res'] = redis.get_indicators(pair, interval, num=3)[0][0]
    DATA[pair]['agg'] = redis.get_agg_data(pair, interval)
    DATA[pair]['sent'] = redis.get_sentiment(pair, interval)

def keepalive():
    """
    Periodically touch file for docker healthcheck
    """
    Path(f'/var/local/lock/gc_get_{config.main.interval}.lock').touch()

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
    setproctitle(f"{config.main.base_env}-get_data-{interval}")
    name = config.main.name.split('-')[-1]
    Path(f'/var/run/{config.main.base_env}-data-{interval}-{name}').touch()

    local_pairs = set(config.main.pairs.split())
    while True:
        # Don't start analysing until all pairs are available
        pairs_request = requests.get(f"http://stream/{config.main.interval}/all", timeout=10)
        if not pairs_request.ok:
            LOGGER.critical("unable to fetch data from streaming server")
        data = pairs_request.json()
        remote_pairs = set(data['recent'].keys())
        if local_pairs.issubset(remote_pairs):
            # we're done
            break
        # not enough pairs,
        LOGGER.info("Waiting for more pairs to become available local:%s, remote:%s",
                    len(local_pairs), len(remote_pairs))
        time.sleep(5)

    if os.path.exists(f'/var/run/{config.main.base_env}-data-{interval}-{name}'):
        os.remove(f'/var/run/{config.main.base_env}-data-{interval}-{name}')

    scheduler = BackgroundScheduler()

    job = scheduler.add_job(func=RUNNER.prod_initial, args=[interval, True, True, 7 ],
                            trigger='interval', seconds=500,
                            next_run_time=datetime.now()+timedelta(seconds=10))
    scheduler.add_job(func=RUNNER.prod_loop, args=[interval, True, True, False],
                      trigger="interval", seconds=120, misfire_grace_time=1000)
    scheduler.add_job(func=keepalive, trigger="interval", seconds=120, misfire_grace_time=1000)
    scheduler.add_job(func=collect_agg_data, args=[interval], trigger="interval",
                      seconds=400, misfire_grace_time=1000)

    for seq, pair in enumerate(PAIRS):
        scheduler.add_job(func=collect_data, args=[pair], trigger="interval",
                          seconds=60, misfire_grace_time=1000, id=str(seq))
    scheduler.start()
    time.sleep(30)
    # initial job only needs to run once - so remove once it has been scheduled and run has begun
    scheduler.remove_job(job.id)

    if float(config.main.logging_level) > 10:
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        log.disabled = True
    APP.run(debug=False, host='0.0.0.0', port=6000, threaded=True)

if __name__ == '__main__':
    main()
