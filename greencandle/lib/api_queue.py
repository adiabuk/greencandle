#!/usr/bin/env python
#pylint: disable=wrong-import-position,no-member,logging-not-lazy,eval-used,broad-except

"""
Function for adding to redis queue
"""

import os
import sys
from time import strftime, gmtime
import requests
from greencandle.lib import config
config.create_config()
from greencandle.lib.redis_conn import Redis
from greencandle.lib.binance_common import get_current_price, get_dataframes
from greencandle.lib.order import Trade
from greencandle.lib.logger import get_logger
from greencandle.lib.common import get_trade_link, get_tv_link
from greencandle.lib.alerts import send_slack_message

LOGGER = get_logger(__name__)
TEST = bool(len(sys.argv) > 1 and sys.argv[1] == '--test')
def add_to_queue(req):
    """
    Add received post request to redis queue to be actioned
    """
    print("action:", req)
    pair = req['pair'].upper().strip()
    action_str = req['action'].upper().strip()
    action = req['action'].strip()
    text = req['text'].strip()
    if not pair:
        send_slack_message("alerts", "Missing pair for api trade")
        return

    LOGGER.info("Request received: %s %s %s" %(pair, action_str, text))
    current_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    try:
        current_price = get_current_price(pair)
    except KeyError:
        message = "Unable to get price for {}".format(pair)
        send_slack_message("alerts", message)
        return

    title = config.main.name + "-manual" if "manual" in req else config.main.name
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
                return

            trend = req.text.strip()
            if trend != config.main.trade_direction and "manual" not in req:
                trade_link = get_trade_link(pair, req['strategy'],
                                            req['action_str'],
                                            "Force trade")
                message = ("Skipping {0} trade due to wrong trade direction ({1})"
                           .format(get_tv_link(pair), trade_link))
                send_slack_message("trades", message)
                LOGGER.info(message)
                return

        result = trade.open_trade(item)
        if result:
            take_profit = float(req['tp']) if 'tp' in req else \
                eval(config.main.take_profit_perc)
            stop_loss = float(req['sl']) if 'sl' in req else \
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
