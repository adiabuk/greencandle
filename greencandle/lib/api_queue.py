#!/usr/bin/env python
#pylint: disable=no-member,eval-used,broad-except,too-many-locals,too-many-statements,logging-fstring-interpolation

"""
Function for adding to redis queue
"""

import os
from time import strftime, gmtime
import requests
from greencandle.lib import config
from greencandle.lib.redis_conn import Redis
from greencandle.lib.binance_common import get_current_price, get_dataframes
from greencandle.lib.order import Trade
from greencandle.lib.logger import get_logger
from greencandle.lib.common import get_trade_link, get_tv_link
from greencandle.lib.alerts import send_slack_message

config.create_config()
LOGGER = get_logger(__name__)

def add_to_queue(req, test=False):
    """
    Add received post request to redis queue to be actioned
    """
    LOGGER.info("action: %s", str(req))
    pair = req['pair'].upper().strip()
    action = str(req['action']).strip()
    text = req['text'].strip()
    take_profit = float(req['tp']) if 'tp' in req and req['tp'] else \
                eval(config.main.take_profit_perc)
    stop_loss = float(req['sl']) if 'sl' in req and req['sl'] else \
                eval(config.main.stop_loss_perc)
    usd = float(req['usd']) if 'usd' in req and req['usd'] else None

    if not pair:
        send_slack_message("alerts", "Missing pair for api trade")
        return

    LOGGER.info("Request received: %s %s %s", pair, str(action), text)
    current_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    try:
        current_price = get_current_price(pair)
    except KeyError:
        message = f"Unable to get price for {pair}"
        send_slack_message("alerts", message)
        return

    title = config.main.name + "-manual" if "manual" in req else config.main.name
    item = [(pair, current_time, current_price, title, action, usd)]
    interval = config.main.interval
    trade = Trade(interval=interval, test_data=False, test_trade=test, config=config)

    try:
        if (config.main.trade_direction == 'long' and float(action) > 0) or \
           (config.main.trade_direction == 'short' and float(action) < 0):
            action_str = 'OPEN'
        else:
            action_str = 'CLOSE'
    except ValueError:
        action_str = str(action).upper().strip()

    redis = Redis(db=2)
    try:
        interval = "1m" if config.main.interval.endswith("s") else config.main.interval
        klines = 60 if interval.endswith('s') or interval.endswith('m') else 5
        dataframes = get_dataframes([pair], interval=interval, no_of_klines=klines)
    except IndexError:
        return

    if action_str == 'OPEN':
        if 'get_trend' in os.environ:
            url = f"http://trend:6001/get_trend?pair={pair}"
            try:
                req = requests.get(url, timeout=1)
            except Exception:
                LOGGER.critical("Unable to get trend from %s", url)
                return

            trend = req.text.strip()
            if trend != config.main.trade_direction and "manual" not in req:
                trade_link = get_trade_link(pair, req['strategy'],
                                            req['action_str'],
                                            "Force trade",
                                            config.web.nginx_port)
                message = (f"Skipping {get_tv_link(pair)} trade due to wrong trade direction "
                           f"({trade_link})")
                send_slack_message("trades", message)
                LOGGER.info(message)
                return

        result = trade.open_trade(item, stop=stop_loss)
        if result or test:
            redis.update_on_entry(item[0][0], 'take_profit_perc', take_profit)
            redis.update_on_entry(item[0][0], 'stop_loss_perc', stop_loss)

            current_candle = dataframes[pair].iloc[-1]
            redis.update_drawdown(pair, current_candle, event="open")
            redis.update_drawup(pair, current_candle, event="open")

    elif action_str == 'CLOSE':
        current_candle = dataframes[pair].iloc[-1]
        redis.update_drawdown(pair, current_candle)
        redis.update_drawup(pair, current_candle)

        drawdown = redis.get_drawdown(pair)['perc']
        drawup = redis.get_drawup(pair)['perc']
        result = trade.close_trade(item, drawdowns={pair:drawdown}, drawups={pair:drawup})

        if not result and not test:
            LOGGER.error(f"Unable to close trade {item}")
