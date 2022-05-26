#!/usr/bin/env python
#pylint: disable=wrong-import-position,no-member,logging-not-lazy

"""
API trading module
"""
import sys
from time import strftime, gmtime
import atexit
from flask import Flask, request, Response
from greencandle.lib.common import arg_decorator
from greencandle.lib import config
config.create_config()
from greencandle.lib.binance_common import get_current_price
from greencandle.lib.run import prod_int_check
from greencandle.lib.logger import get_logger
from greencandle.lib.order import Trade
from apscheduler.schedulers.background import BackgroundScheduler


TEST = bool(len(sys.argv) > 1 and sys.argv[1] == '--test')
APP = Flask(__name__)
LOGGER = get_logger(__name__)

@APP.route('/webhook', methods=['POST'])
def respond():
    """
    Default route to trade
    """
    print("action:", request.json)
    pair = request.json['pair'].upper()
    action = request.json['action'].upper()
    text = request.json['text']
    LOGGER.info("Request received: %s %s %s" %(pair, action, text))
    current_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    current_price = get_current_price(pair)
    item = [(pair, current_time, current_price, config.main.name)]
    trade = Trade(interval=config.main.interval, test_data=False, test_trade=TEST, config=config)

    try:
        if (config.main.trade_direction == 'long' and float(action) > 0) or \
              (config.main.trade_direction == 'short' and float(action) < 0):
            action = 'OPEN'
        else:
            action = 'CLOSE'
    except ValueError:
        pass

    if action == 'OPEN':
        trade.open_trade(item)
        redis = Redis(interval=config.main.interval, test=False, test_data=False)
        redis.update_on_entry(item[0][0], 'take_profit_perc', eval(config.main.take_profit_perc))
        redis.update_on_entry(item[0][0], 'stop_loss_perc', eval(config.main.stop_loss_perc))

    elif action == 'CLOSE':
        trade.close_trade(item, drawdowns={pair:0}, drawups={pair:0})
        redis = Redis(interval=config.main.interval, test=False, test_data=False)
        redis.rm_on_entry(item[0][0], 'take_profit_perc')
        redis.rm_on_entry(item[0][0], 'stop_loss_perc')

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
    prod_int_check(config.main.interval, True, alert=True)

@arg_decorator
def main():
    """
    Receives trade requests from web front-end/API/router and
    open/close trade as appropriate

    Usage: backend_api
    """

    scheduler = BackgroundScheduler()
    scheduler.add_job(func=intermittent_check, trigger="interval", seconds=60)
    scheduler.start()
    APP.run(debug=True, host='0.0.0.0', port=20000, threaded=True)

    # Shut down the scheduler when exiting the app
    atexit.register(scheduler.shutdown)

if __name__ == "__main__":
    main()
