#!/usr/bin/env python
#pylint: disable=no-member,eval-used,unused-import,global-statement,no-name-in-module

"""
Analyze available data from redis
Look for potential trades
"""
import gc
import os
import time
import glob
import json
import sys
from datetime import datetime
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import requests
from send_nsca3 import send_nsca
from str2bool import str2bool
from setproctitle import setproctitle
from greencandle.lib import config
from greencandle.lib.redis_conn import Redis
from greencandle.lib.mysql import Mysql
from greencandle.lib.logger import get_logger, exception_catcher
from greencandle.lib.alerts import send_slack_message
from greencandle.lib.common import (get_tv_link, arg_decorator, convert_to_seconds, perc_diff,
                                    get_trailing_number)
from greencandle.lib.auth import binance_auth
from greencandle.lib.order import Trade
from greencandle.lib.web import decorator_timer, retry_session
from greencandle.lib.objects import AttributeDict

config.create_config()
INTERVAL = config.main.interval
STRAT_NO = get_trailing_number(config.main.name)
DIRECTION = config.main.trade_direction
LOGGER = get_logger(__name__)
PAIRS = config.main.pairs.split()
MAIN_INDICATORS = config.main.indicators.split()
GET_EXCEPTIONS = exception_catcher((Exception))
TRIGGERED = {}
DATA = {}

if sys.argv[-1] != "--help":
    CLIENT = binance_auth()
    ISOLATED = CLIENT.get_isolated_margin_pairs()
    CROSS = CLIENT.get_cross_margin_pairs()
else:
    ISOLATED = None
    CROSS = None
STORE_IN_DB = bool('STORE_IN_DB' in os.environ)
CHECK_REDIS_PAIR = int(os.environ['CHECK_REDIS_PAIR']) if 'CHECK_REDIS_PAIR' in \
        os.environ else False
CHECK_REDIS_INTERVAL = os.environ['CHECK_REDIS_INTERVAL'] if 'CHECK_REDIS_INTERVAL' in \
        os.environ else False
ROUTER_FORWARD = bool('ROUTER_FORWARD' in os.environ)
REDIS_FORWARD = [int(x) for x in os.environ['REDIS_FORWARD'].split(',')] if 'REDIS_FORWARD' \
        in os.environ else False

@decorator_timer
def analyse_loop():
    """
    Gather data from redis and analyze
    """
    global DATA
    LOGGER.debug("recently triggered: %s", str(TRIGGERED))

    lock_file= f'/var/run/{config.main.base_env}-{INTERVAL}-get'

    if glob.glob(lock_file):
        while True:
            LOGGER.info("waiting for initial data collection to complete for %s", INTERVAL)
            if not glob.glob(lock_file):
                LOGGER.info("finished initial data collection for %s", INTERVAL)
                break
            time.sleep(30)

    LOGGER.debug("start of current loop")
    redis = Redis()
    if STORE_IN_DB:
        dbase = Mysql(interval=INTERVAL)
        open_pairs = dbase.fetch_sql_data(f'select pair, comment, 999999 from trades where '
                                          f'`interval`="{INTERVAL}" and '
                                          f'name="{config.main.name}" and '
                                          f'close_price is null', header=False)
        open_pairs = [tuple(x) for x in open_pairs]
        del dbase
    else:
        open_pairs = []

    if CHECK_REDIS_PAIR:
        redis4=Redis(db=CHECK_REDIS_PAIR)
        new_interval = CHECK_REDIS_INTERVAL if CHECK_REDIS_INTERVAL else INTERVAL
        redis_pairs = [x.decode().split(':') for x in
                       redis4.conn.smembers(f'{new_interval}:{DIRECTION}')]
        redis_pairs = [tuple(x) for x in redis_pairs]

        # check if pair to be analysed is already open

        for pair, reversal, expire in redis_pairs:
            if int(config.redis.redis_expiry_seconds) > 0 and \
                    int(time.time()) > (int(config.redis.redis_expiry_seconds)  +
                                        int(float(expire))):
                LOGGER.info("trade expired %s:%s:%s - removing from redis db:%s", pair, reversal,
                            expire, CHECK_REDIS_PAIR)
                redis4.conn.srem(f'{INTERVAL}:{DIRECTION}', f'{pair}:{reversal}:{expire}')
                redis_pairs.remove((pair, reversal, expire))
                # remove from redis_pairs

        # union
        pairs = redis_pairs + [x for x in open_pairs if (x[0] not in [y[0] for y in redis_pairs])]

        # intersection
        common = [x for x in redis_pairs if (x[0] in [y[0] for y in open_pairs])]

        for pair in common:
            # close trade when so we can re-fire open signal
            trade = Trade(interval=INTERVAL, test_trade=True, test_data=False, config=config)
            details = [[pair[0], "2020-01-01 00:00:00", "0.0001", "reopen", "0", 'None']]
            if pair[1] != 'reversal':
                trade.close_trade(details)

    else:
        # not being fetched from redis db
        pairs = [(pair, 'normal', 999999) for pair in PAIRS]
    session = retry_session(retries=5, backoff_factor=2)
    DATA = session.request('GET', f'http://www.data.amrox.loc/data/{INTERVAL}',
                           timeout=20).json()['output']
    with ThreadPoolExecutor(max_workers=50) as pool:
        for pair, reversal, expire in pairs:
            pool.submit(analyse_pair, pair, reversal, expire, redis)
    pool.shutdown(wait=True)
    LOGGER.info("end of current loop")
    Path(f'/var/local/lock/{config.main.name}').touch()
    gc.collect()
    del redis
    if CHECK_REDIS_PAIR:
        time.sleep(5)
    else:
        time.sleep(1)

def get_match_name(matches):
    """
    get a list of matching rule names based on container number, and matching rule number
    """
    match_names = []
    try:
        container_num = int(config.main.name[len(config.main.name.rstrip('0123456789')):])
    except ValueError:
        container_num = 1

    name_lookup = [['trend_200', 'golden_cross', 'new_golden'],
                   ['old_stoch'],
                   ['distance', 'bb', "bbperc_diff", "bbperc_extreme"],
                   ['low_rsi_in_trend_near_EMA', 'low_rsi_in_trend'],
                   ['STOCHRSI_flip','RSI_close-rule','broken_trend','multi_ind_close','re-xover'],
                   ['smi_confirm'],
                   ['ema_xover'],
                   ['rsi_cross_multi_reversal'],
                   ['empty9'],
                   ['empty10'],
                   ['empty11'],
                   ['MACD_volume', 'EMA_volume'],
                   ['empty_13'],
                   ['RSI_flip'],
                   ['RSI_1d'],
                   ['RSI_1h', 'RSI_1h+bb'],
                   ['outside+high_atr']
                   ]
    for match in matches:
        match_names.append(name_lookup[container_num-1][match-1])
    return ','.join(match_names)

@decorator_timer
def analyse_pair(pair, reversal, expire, redis):
    """
    Analysis of individual pair
    """

    supported = ""
    if DIRECTION != "short":
        supported += "spot "

    supported += "isolated " if pair in ISOLATED else ""
    supported += "cross " if pair in CROSS else ""

    if not supported.strip():
        # don't analyse pair if spot/isolated/cross not supported
        return

    LOGGER.debug("analysing pair: %s", pair)
    res = [AttributeDict(x) for x in DATA[pair]['res']]
    items = DATA[pair]['items']
    agg = AttributeDict(DATA[pair]['agg'])
    sent = DATA[pair]['sent']
    output = redis.get_rule_action(pair=pair, interval=INTERVAL, res=res, agg=agg, sent=sent,
                                   items=items, check_reversal=True)
    result, _, current_time, current_price, match = output
    event = reversal
    flip = match['reversal']
    LOGGER.debug("analysis result for %s is %s", pair, str(output))

    if result in ('OPEN', 'CLOSE'):
        LOGGER.info("analysis result for %s is %s", pair, str(output))
        LOGGER.debug("trades to %s for pair %s", result.lower(), pair)
        now = datetime.now()

        # Only alert on a given pair once per hour
        # for each strategy
        if pair in TRIGGERED:
            diff = now - TRIGGERED[pair]
            diff_in_hours = diff.total_seconds() / 3600
            if str2bool(config.main.wait_between_trades) and diff.total_seconds() < \
                    convert_to_seconds(config.main.time_between_trades):
                LOGGER.debug("skipping notification for %s %s as recently triggered",
                             pair, INTERVAL)
                return
            LOGGER.debug("triggering alert: last alert %s hours ago", diff_in_hours)

        TRIGGERED[pair] = now
        try:
            match_strs = get_match_name(match[result.lower()])
        except IndexError:
            match_strs = match[result.lower()]
        msg = (f"{result.lower()}, {match_strs}: {get_tv_link(pair, INTERVAL)} "
               f"{INTERVAL} {config.main.name} ({supported.strip()}) - {current_time}\n"
               f"Data: {res[0]}\nAgg: {agg}\nsent: {sent}")

        if result == 'OPEN':
            send_slack_message("notifications", msg, emoji=True,
                               icon=f':{INTERVAL}-{DIRECTION}:')
        if 'NSCA' in os.environ:
            send_nsca(status=0, host_name='datavault', service_name=f"data_{DIRECTION}",
                      text_output="OK", remote_host='nagios.amrox.loc')

        if DIRECTION == 'long' and result == 'OPEN':
            action = 1
        elif DIRECTION == 'short' and result == 'OPEN':
            action = -1
        else:
            action = 0


        details = [[pair, current_time, current_price, event, action, None]]
        trade = Trade(interval=INTERVAL, test_trade=True, test_data=False, config=config)
        if result == 'OPEN' and STORE_IN_DB:
            LOGGER.info("opening data trade for %s", pair)
            trade.open_trade(details)
        elif result == 'CLOSE' and STORE_IN_DB:
            if reversal == 'normal':
                LOGGER.info("closing normal trade for %s", pair)
                trade.close_trade(details)

                current_name = config.main.name
                current_direction = config.main.trade_direction
                new_name = current_name.replace('short', 'long') if \
                        current_direction=='short' else current_name.replace('long', 'short')
                new_direction = current_direction.replace('short', 'long') if \
                        current_direction=='short' else current_name.replace('long', 'short')
                command = (f"delete from trades where name like '%{current_name}%' "
                           f"and direction='{current_direction}'")
                command2 = (f"delete from trades where name like '%{new_name}%' "
                            f"and direction='{new_direction}'")
                dbase = Mysql()
                dbase.run_sql_statement(command)
                dbase.run_sql_statement(command2)
                del dbase

            else:
                LOGGER.info("not closing reversal trade for %s", pair)

        if CHECK_REDIS_PAIR and result=='OPEN':
            redis4 = Redis(db=CHECK_REDIS_PAIR)
            redis4.conn.srem(f'{INTERVAL}:{DIRECTION}', f'{pair}:{reversal}:{expire}')
            del redis4
            LOGGER.info("trade opening %s:%s:%s - removing from redis db:%s", pair, reversal,
                        expire, CHECK_REDIS_PAIR)

        directions = {'short':-1, 'long':1}
        if flip:
            del directions[DIRECTION]
            new_direction = list(directions.keys())[0]
            new_action = list(directions.values())[0]
            reversal = 'reversal'
            LOGGER.info("Flipping direction from %s to %s for pair %s", DIRECTION,
                        new_direction, pair)
        else:
            new_direction = DIRECTION
            new_action = directions[DIRECTION]
            reversal = 'normal'

        if ROUTER_FORWARD and not flip:
            url = f"http://router:1080/{config.web.api_token}"
            forward_strategy = f'{INTERVAL}-{STRAT_NO}'
            payload = {"pair": pair,
                       "text": (f"forwarding {result.lower()} trade from "
                                f"{match_strs}/{INTERVAL}/{DIRECTION}"),
                       "sl": eval(config.main.stop_loss_perc) if new_direction=='long' else \
                               eval(config.main.take_profit_perc),
                       "tp": 2*eval(config.main.stop_loss_perc) if new_direction=='long' else \
                               2*eval(config.main.take_profit_perc),
                       "interval": config.main.interval,
                       "action": str(new_action),
                       "env": config.main.name,
                       "price": current_price,
                       "strategy": forward_strategy}

            try:
                requests.post(url, json.dumps(payload), timeout=20,
                              headers={'Content-Type': 'application/json'})
                LOGGER.info("forwarding %s %s/%s trade to: %s match:%s",
                            pair, INTERVAL, new_direction, forward_strategy, match_strs)

            except requests.exceptions.RequestException:
                LOGGER.warning("Unable to forward trade %s %s/%s trade to: %s match:%s",
                                pair, INTERVAL, new_direction, forward_strategy, match_strs)

        if result == 'OPEN' and REDIS_FORWARD and flip:
            for forward_db in REDIS_FORWARD:
                redis4 = Redis(db=forward_db)
                # add to redis set
                LOGGER.info("new forward trade adding %s to %s:%s set db %s",
                            pair, INTERVAL, DIRECTION, forward_db)
                redis_pairs = [x.decode().split(':') for x
                               in redis4.conn.smembers(f'{INTERVAL}:{new_direction}')]

                # check pair doesn't already exist
                if not [el for el in redis_pairs if el[0] == pair and el[1] == reversal]:
                    now = int(time.time())
                    redis4.conn.sadd(f'{INTERVAL}:{new_direction}', f'{pair}:{reversal}:{now}')
                del redis4

        LOGGER.info("trade alert: %s %s %s %s %s (%s)",result, pair, match_strs, INTERVAL,
                    new_direction, supported.strip())

@arg_decorator
def main():
    """
    Analyse data from redis and alert to slack if there are current trade opportunities
    Required: CONFIG_ENV var and config

    Usage: analyse_data
    """
    fwd_str = "-forward" if ROUTER_FORWARD else ''
    container_no = config.main.name[-1]

    setproctitle(f"{config.main.base_env}-analyse_data{container_no}-{INTERVAL}{fwd_str}")

    while True:
        analyse_loop()
        time.sleep(int(config.main.check_interval))

if __name__ == "__main__":
    main()
