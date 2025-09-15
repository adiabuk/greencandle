#!/usr/bin/env python
#pylint: disable=no-member,eval-used,broad-except,too-many-locals,too-many-statements,logging-fstring-interpolation

"""
Function for adding to redis queue
"""
import os
from time import strftime, gmtime
import requests
import pandas
from greencandle.lib import config
from greencandle.lib.redis_conn import Redis
from greencandle.lib.mysql import Mysql
from greencandle.lib.binance_accounts import get_local_price
from greencandle.lib.binance_common import get_dataframes
from greencandle.lib.order import Trade
from greencandle.lib.logger import get_logger
from greencandle.lib.common import get_trade_link, get_tv_link
from greencandle.lib.alerts import send_slack_message
from greencandle.lib.web import retry_session
from greencandle.lib.sentiment import Sentiment

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
        LOGGER.error("Missing pair for api trade %s", str(req))
        return

    LOGGER.info("Request received: %s %s %s", pair, str(action), text)
    current_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    try:
        current_price = get_local_price(pair)
    except KeyError:
        message = f"Unable to get price for {pair}"
        send_slack_message("alerts", message)
        return

    title = config.main.name + "-manual" if "manual" in req['text'] else config.main.name
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
    dbase = Mysql(interval=config.main.interval)
    try:

        url = f'http://stream/{config.main.interval}/recent?pair={pair}'
        session = retry_session(retries=5, backoff_factor=2)
        req = session.request('GET', url, timeout=30)
        current_candle = pandas.Series(req.json())
    except ConnectionError:
        LOGGER.critical("Unable to get candle for %s from stream, trying conventional method", pair)
        try:
            interval = "1m" if config.main.interval.endswith("s") else config.main.interval
            klines = 60 if interval.endswith('s') or interval.endswith('m') else 5
            dataframes = get_dataframes([pair], interval=interval, no_of_klines=klines)
            current_candle = dataframes[pair].iloc[-1]
        except IndexError:
            LOGGER.critical("Unable to get candle from binance, giving up")
            return

    if action_str == 'OPEN':
        sentiment = Sentiment()
        if sentiment.get_results():
            LOGGER.info("Sentiment matches for %s, proceeding...", pair)
        else:
            LOGGER.critical("No matching sentiment for %s, skipping....", pair)
            return

        if 'get_trend' in os.environ:
            url = f"http://trend:6001/get_trend?pair={pair}"
            try:
                req = requests.get(url, timeout=20)
            except Exception:
                LOGGER.critical("Unable to get trend from %s", url)
                return

            trend = req.text.strip()
            if trend != config.main.trade_direction and "manual" not in req['text']:
                trade_link = get_trade_link(pair, req['strategy'],
                                            req['action_str'],
                                            "Force trade", base_env=config.main.base_env)
                message = (f"Skipping {get_tv_link(pair)} trade due to wrong trade direction "
                           f"({trade_link})")
                send_slack_message("trades", message)
                LOGGER.info(message)
                return

        result = trade.open_trade(item, stop=stop_loss)
        if result == "opened":
            redis.update_on_entry(item[0][0], 'take_profit_perc', take_profit)
            redis.update_on_entry(item[0][0], 'stop_loss_perc', stop_loss)

            redis.update_drawdown(pair, current_candle, event="open")
            redis.update_drawup(pair, current_candle, event="open")

    elif action_str == 'CLOSE' and dbase.get_quantity(pair):
        redis.update_drawdown(pair, current_candle)
        redis.update_drawup(pair, current_candle)

        drawdown = redis.get_drawdown(pair)['perc']
        drawup = redis.get_drawup(pair)['perc']
        result = trade.close_trade(item, drawdowns={pair:drawdown}, drawups={pair:drawup})

        if not result:
            if test:
                LOGGER.info(f"Unable to close trade {item}")
            else:
                LOGGER.error(f"Unable to close trade {item}")
