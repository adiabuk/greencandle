#!/usr/bin/env python
#pylint: disable=no-member
"""
Flask module for getting indicator values
"""
import logging
from collections import defaultdict
from flask import Flask, request, Response
from greencandle.lib import config
from greencandle.lib.common import arg_decorator
from greencandle.lib.redis_conn import Redis

config.create_config()
LONG = set()
SHORT = set()
ALL = defaultdict(dict)
PAIRS = config.main.pairs.split()
APP = Flask(__name__, template_folder="/var/www/html", static_url_path='/',
            static_folder='/var/www/html')

@APP.route('/healthcheck', methods=["GET"])
def healthcheck():
    """
    Docker healthcheck
    Return 200
    """
    return Response(status=200)

@APP.route('/get_value', methods=["POST"])
def get_value():
    """
    Get result of indicator for given pair/timeframe within current scope/server
    works accross multiple timeframes

    Returns result of redis query
    """
    payload = request.json
    redis = Redis()
    item = redis.get_items(payload['pair'], payload['interval'])[-1]
    result = redis.get_result(item, payload['indicator'])
    return result

@arg_decorator
def main():
    """
    API for determining getting values from various strategies and timeframes
    """
    logging.basicConfig(level=logging.ERROR)
    if float(config.main.logging_level) > 10:
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        log.disabled = True
    APP.run(debug=False, host='0.0.0.0', port=6000, threaded=True)

if __name__ == '__main__':
    main()
