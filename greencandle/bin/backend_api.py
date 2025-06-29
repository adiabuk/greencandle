#!/usr/bin/env python
#pylint: disable=no-member,no-name-in-module

"""
API trading module
"""
import os
import sys
import atexit
import logging
from flask import Flask, request, Response
from apscheduler.schedulers.background import BackgroundScheduler
from rq import Queue, Worker
from setproctitle import setproctitle
from greencandle.lib import config
from greencandle.lib.run import ProdRunner
from greencandle.lib.redis_conn import Redis
from greencandle.lib.mysql import Mysql
from greencandle.lib.common import arg_decorator
from greencandle.lib.logger import get_logger
from greencandle.lib.api_queue import add_to_queue
from greencandle.lib.web import decorator_timer

config.create_config()
TEST = bool(len(sys.argv) > 1 and sys.argv[1] == '--test')
APP = Flask(__name__)
LOGGER = get_logger(__name__)

def consume_queue():
    """
    Process redis queue
    """
    redis = Redis(db=1)
    name = f"{config.main.name}-{config.main.trade_direction}"
    queue = Queue(connection=redis.conn, name=name)
    worker = Worker([queue], connection=redis.conn)
    worker.work()

@APP.route('/webhook', methods=['POST'])
def respond():
    """
    Default route to trade
    """
    redis = Redis(db=1)
    name = f"{config.main.name}-{config.main.trade_direction}"
    queue = Queue(connection=redis.conn, name=name)
    queue.enqueue(add_to_queue, request.json, TEST, result_ttl=60)
    return Response(status=200)

@APP.route('/healthcheck', methods=["GET"])
def healthcheck():
    """
    Docker healthcheck
    Return 200
    """
    return Response(status=200)

@APP.route('/close_all', methods=['POST'])
def close_all():
    """
    Close all trades
    """
    req = request.json
    dbase = Mysql()
    redis = Redis(db=1)
    name = f"{config.main.name}-{config.main.trade_direction}"
    queue = Queue(connection=redis.conn, name=name)
    open_trades = dbase.get_open_trades(name_filter=req['interval'],
                                        direction_filter=req['direction'],
                                        header=False)
    LOGGER.info("Close all request received: %s, %s trades to close", str(req), len(open_trades))
    for trade in open_trades:
        _, interval, pair, name, _, _, _ = trade
        payload = {'pair': pair, 'text': 'closing from close_all api call', 'interval': interval,
                   'action': 0, 'env': config.main.base_env, 'price': 'none', 'strategy':
                   req['strategy'], 'edited': 'no'}
        queue.enqueue(add_to_queue, payload, TEST, result_ttl=60)
    return Response(status=200)

@decorator_timer
def intermittent_check():
    """
    Check for SL/TP
    """
    LOGGER.debug("starting prod int check")
    alert = bool('ALERT' in os.environ)
    runner = ProdRunner()
    runner.prod_int_check(config.main.interval, True, alert=alert)
    LOGGER.debug("finished prod int check")

@arg_decorator
def main():
    """
    Receives trade requests from web front-end/API/router and
    open/close trade as appropriate

    Usage: backend_api [--test] [api|queue]
    """
    test_str = '-test' if TEST else ''
    setproctitle(f"{config.main.base_env}-backend_api-{sys.argv[-1]}{test_str}")
    if sys.argv[-1] == 'api':
        if "intermittent" in os.environ:
            scheduler = BackgroundScheduler()
            scheduler.add_job(func=intermittent_check, trigger="interval", seconds=120,
                              misfire_grace_time=120)
            scheduler.start()
        if float(config.main.logging_level) > 10:
            log = logging.getLogger('werkzeug')
            log.setLevel(logging.ERROR)
            log.disabled = True
        logging.basicConfig(level=logging.ERROR)
        APP.run(debug=False, host='0.0.0.0', port=20000, threaded=True)
    else:
        consume_queue()

    if "intermittent" in os.environ and sys.argv[-1] == 'api':
        # Shut down the scheduler when exiting the app
        atexit.register(scheduler.shutdown)

if __name__ == "__main__":
    main()
