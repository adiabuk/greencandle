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
    action_str = request.json['action'].upper()
    text = request.json['text']
    if not pair:
        send_slack_message("alerts", "Missing pair for api trade")
        return Response(status=200)

    LOGGER.info("Request received: %s %s %s" %(pair, action_str, text))
    current_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    try:
        current_price = get_current_price(pair)
    except KeyError:
        message = "Unable to get price for {}".format(pair)
        send_slack_message("alerts", message)
        return Response(status=200)

    title = config.main.name + "-manual" if "manual" in request.json else config.main.name
    item = [(pair, current_time, current_price, title, action)]
    trade = Trade(interval=config.main.interval, test_data=False, test_trade=TEST, config=config)

    try:
        if (config.main.trade_direction == 'long' and float(action) > 0) or \
           (config.main.trade_direction == 'short' and float(action) < 0):
            action_str = 'OPEN'
        else:
            action_str = 'CLOSE'
    except ValueError:
        pass

    redis = Redis()
    if action_str == 'OPEN':

        if 'get_trend' in os.environ:
            url = "http://trend:6001/get_trend?pair={}".format(pair)
            try:
                req = requests.get(url, timeout=1)
            except Exception:
                LOGGER.error("Unable to get trend from %s" % url)
                return Response(status=500)

            trend = req.text.strip()
            if trend != config.main.trade_direction and "manual" not in request.json:
                trade_link = get_trade_link(pair, request.json['strategy'],
                                            request.json['action_str'],
                                            "Force trade")
                message = ("Skipping {0} trade due to wrong trade direction ({1})"
                           .format(get_tv_link(pair), trade_link))
                send_slack_message("trades", message)
                LOGGER.info(message)
                return Response(status=200)

        result = trade.open_trade(item)
        if result:
            take_profit = float(request.json['tp']) if 'tp' in request.json else \
                eval(config.main.take_profit_perc)
            stop_loss = float(request.json['sl']) if 'sl' in request.json else \
                eval(config.main.stop_loss_perc)

            redis.update_on_entry(item[0][0], 'take_profit_perc', take_profit)
            redis.update_on_entry(item[0][0], 'stop_loss_perc', stop_loss)

            interval = "1m" if config.main.interval.endswith("s") else config.main.interval
            dataframes = get_dataframes([pair], interval=interval, no_of_klines=1)
            current_candle = dataframes[pair].iloc[-1]
            redis.update_drawdown(pair, current_candle, event="open")
            redis.update_drawup(pair, current_candle, event="open")

    elif action_str == 'CLOSE':
        drawdown = redis.get_drawdown(pair)
        drawup = redis.get_drawup(pair)['perc']
        result = trade.close_trade(item, drawdowns={pair:drawdown}, drawups={pair:drawup})
        if result:
            redis = Redis()
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
    if "intermittent" in os.environ:
        scheduler = BackgroundScheduler()
        scheduler.add_job(func=intermittent_check, trigger="interval", seconds=30)
        scheduler.start()

    APP.run(debug=False, host='0.0.0.0', port=20000, threaded=True)


    if "intermittent" in os.environ:
        # Shut down the scheduler when exiting the app
        atexit.register(scheduler.shutdown)

if __name__ == "__main__":
    main()
