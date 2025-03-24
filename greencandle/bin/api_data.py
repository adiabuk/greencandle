#!/usr/bin/env python
#pylint: disable=no-member,no-name-in-module
"""
Collect OHLC and strategy data for later analysis
"""
from pathlib import Path
from collections import defaultdict
from setproctitle import setproctitle
from flask import Flask, request, Response, jsonify
from apscheduler.schedulers.background import BackgroundScheduler
from greencandle.lib import config
from greencandle.lib.redis_conn import Redis
from greencandle.lib.run import ProdRunner
from greencandle.lib.logger import get_logger, exception_catcher
from greencandle.lib.common import arg_decorator

config.create_config()
LOGGER = get_logger(__name__)
PAIRS = config.main.pairs.split()
MAIN_INDICATORS = config.main.indicators.split()
GET_EXCEPTIONS = exception_catcher((Exception))
RUNNER = ProdRunner()
APP = Flask(__name__, template_folder="/var/www/html", static_url_path='/',
            static_folder='/var/www/html')
DATA = defaultdict(lambda: defaultdict(dict))

def set_data():
    """
    Update data
    """
    redis = Redis()
    interval = config.main.interval
    for pair in PAIRS:
        DATA[pair]['res'], DATA[pair]['items'] = redis.get_indicators(pair, interval, num=7)
        DATA[pair]['agg'] = redis.get_agg_data(pair, interval)
        DATA[pair]['sent'] = redis.get_sentiment(pair, interval)

    return Response(status=200)

@APP.route('/get_data', methods=["GET"])
def get_data():
    """
    Retrieve data
    """
    pair = request.args.get('pair')
    data_type = request.args.get('type')
    interval = request.args.get('interval')
    print("xxx", pair, data_type, interval)

    try:
        if not (pair or data_type):
            return jsonify(output=DATA)
        return jsonify(output=DATA[pair][data_type])
    except KeyError:
        return {}

def keepalive():
    """
    Periodically touch file for docker healthcheck
    """
    Path(f'/var/local/lock/gc_get_{config.main.interval}.lock').touch()

@APP.route('/healthcheck', methods=["GET"])
def healthcheck():
    """
    Docker healthcheck
    Return 200
    """
    return Response(status=200)

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


    #if float(config.main.logging_level) > 10:
    #    log = logging.getLogger('werkzeug')
    #    log.setLevel(logging.ERROR)
    #    log.disabled = True
    scheduler = BackgroundScheduler() # Create Scheduler
    scheduler.add_job(func=set_data, trigger="interval", minutes=3, misfire_grace_time=120)
    scheduler.start()

    APP.run(debug=False, host='0.0.0.0', port=6000, threaded=True)

if __name__ == '__main__':
    main()
