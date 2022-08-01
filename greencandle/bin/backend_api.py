#!/usr/bin/env python
#pylint: disable=wrong-import-position,no-member,logging-not-lazy,eval-used,broad-except

"""
API trading module
"""
import os
import sys
from time import strftime, gmtime
import atexit
import requests
from flask import Flask, request, Response
from apscheduler.schedulers.background import BackgroundScheduler
from greencandle.lib.common import arg_decorator, get_tv_link, get_trade_link
from greencandle.lib import config
config.create_config()
from greencandle.lib.binance_common import get_current_price, get_dataframes
from greencandle.lib.run import prod_int_check
from greencandle.lib.redis_conn import Redis
from greencandle.lib.logger import get_logger
from greencandle.lib.order import Trade
from greencandle.lib.alerts import send_slack_message

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

    title = config.main.name + "-manual" if "manual" in request.json else config.main.name
    item = [(pair, current_time, current_price, title)]
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

        if 'get_trend' in os.environ:
            url = "http://trend:6001/get_trend?pair={}".format(pair)
            try:
                req = requests.get(url, timeout=1)
            except Exception:
                LOGGER.error("Unable to get trend from %s" % url)
                return Response(status=500)

            trend = req.text.strip()
            if trend != config.main.trade_direction and "manual" not in request.json:
                trade_link = get_trade_link(pair, request.json['strategy'], request.json['action'],
                                            "Force trade")
                message = ("Skipping {0} trade due to wrong trade direction ({1})"
                           .format(get_tv_link(pair), trade_link))
                send_slack_message("trades", message)
                LOGGER.info(message)
                return Response(status=200)

        trade.open_trade(item)
        redis = Redis()
        redis.update_on_entry(item[0][0], 'take_profit_perc', eval(config.main.take_profit_perc))
        redis.update_on_entry(item[0][0], 'stop_loss_perc', eval(config.main.stop_loss_perc))
        interval = "1m" if config.main.interval.endswith("s") else config.main.interval
        dataframes = get_dataframes([pair], interval=interval, no_of_klines=1)
        current_candle = dataframes[pair].iloc[-1]
        redis.update_drawdown(pair, current_candle, event="open")
        redis.update_drawup(pair, current_candle, event="open")

    elif action == 'CLOSE':
        redis = Redis()
        drawdown = redis.get_drawdown(pair)
        drawup = redis.get_drawup(pair)['perc']
        trade.close_trade(item, drawdowns={pair:drawdown}, drawups={pair:drawup})
        redis.rm_on_entry(item[0][0], 'take_profit_perc')
        redis.rm_on_entry(item[0][0], 'stop_loss_perc')
        redis.rm_drawup(pair)
        redis.rm_drawdown(pair)

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
    if "intermittent" in os.environ:
        scheduler = BackgroundScheduler()
        scheduler.add_job(func=intermittent_check, trigger="interval", seconds=60)
        scheduler.start()

    APP.run(debug=False, host='0.0.0.0', port=20000, threaded=True)


    if "intermittent" in os.environ:
        # Shut down the scheduler when exiting the app
        atexit.register(scheduler.shutdown)

if __name__ == "__main__":
    main()
