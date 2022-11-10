#!/usr/bin/env python
#pylint: disable=wrong-import-position,no-member,logging-not-lazy,eval-used,broad-except

"""
API trading module
"""
import os
import sys
import atexit
from flask import Flask, request, Response
from apscheduler.schedulers.background import BackgroundScheduler
from rq import Queue, Worker
from greencandle.lib import config
config.create_config()
from greencandle.lib.run import prod_int_check
from greencandle.lib.redis_conn import Redis
from greencandle.lib.common import arg_decorator
from greencandle.lib.logger import get_logger
from greencandle.lib.api_queue import add_to_queue

TEST = bool(len(sys.argv) > 1 and sys.argv[1] == '--test')
APP = Flask(__name__)
LOGGER = get_logger(__name__)

def consume_queue():
    """
    Process redis queue
    """
    redis = Redis()
    name = "{}-{}".format(config.main.name, config.main.trade_direction)
    queue = Queue(connection=redis.conn, name=name)
    worker = Worker([queue], connection=redis.conn)
    worker.work()

@APP.route('/webhook', methods=['POST'])
def respond():
    """
    Default route to trade
    """
    redis = Redis()
    name = "{}-{}".format(config.main.name, config.main.trade_direction)
    queue = Queue(connection=redis.conn, name=name)
    queue.enqueue(add_to_queue, request.json)
    return Response(status=200)

@APP.route('/healthcheck', methods=["GET"])
def healthcheck():
    """
    Docker healthcheck
    Return 200
    """
    return Response(status=200)

def intermittent_check():
    """
    Check for SL/TP
    """
    LOGGER.info("Starting prod int check")
    alert = bool('HOST_IP' in os.environ)
    prod_int_check(config.main.interval, True, alert=alert)
    LOGGER.info("Finished prod int check")

@arg_decorator
def main():
    """
    Receives trade requests from web front-end/API/router and
    open/close trade as appropriate

    Usage: backend_api
    """

    if sys.argv[2] == 'api':
        if "intermittent" in os.environ:
            scheduler = BackgroundScheduler()
            scheduler.add_job(func=intermittent_check, trigger="interval", seconds=30)
            scheduler.start()
        APP.run(debug=False, host='0.0.0.0', port=20000, threaded=True)
    else:
        consume_queue()


    if "intermittent" in os.environ and sys.argv[2] == 'api':
        # Shut down the scheduler when exiting the app
        atexit.register(scheduler.shutdown)

if __name__ == "__main__":
    main()
