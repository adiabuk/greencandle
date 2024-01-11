#!/usr/bin/env python
#pylint: disable=no-member,global-statement,too-many-locals,broad-except

"""
Analyze available data from redis
Look for potential trades
"""
import os
import time
import glob
import json
import sys
from datetime import datetime
from pathlib import Path
import requests
import setproctitle
from str2bool import str2bool
from send_nsca3 import send_nsca
from greencandle.lib import config
from greencandle.lib.redis_conn import Redis
from greencandle.lib.mysql import Mysql
from greencandle.lib.logger import get_logger, exception_catcher
from greencandle.lib.alerts import send_slack_message
from greencandle.lib.common import get_tv_link, arg_decorator, convert_to_seconds
from greencandle.lib.auth import binance_auth
from greencandle.lib.order import Trade

config.create_config()
INTERVAL = config.main.interval
DIRECTION = config.main.trade_direction
LOGGER = get_logger(__name__)
PAIRS = config.main.pairs.split()
MAIN_INDICATORS = config.main.indicators.split()
GET_EXCEPTIONS = exception_catcher((Exception))
TRIGGERED = {}

if sys.argv[-1] != "--help":
    CLIENT = binance_auth()
    ISOLATED = CLIENT.get_isolated_margin_pairs()
    CROSS = CLIENT.get_cross_margin_pairs()
    STORE_IN_DB = bool('STORE_IN_DB' in os.environ)
    CHECK_REDIS_PAIR = int(os.environ['CHECK_REDIS_PAIR']) if 'CHECK_REDIS_PAIR' in \
            os.environ else False
    ROUTER_FORWARD = bool('ROUTER_FORWARD' in os.environ)
    REDIS_FORWARD = [int(x) for x in os.environ['REDIS_FORWARD'].split(',')] if 'REDIS_FORWARD' \
            in os.environ else False

@GET_EXCEPTIONS
def analyse_loop():
    """
    Gather data from redis and analyze
    """
    LOGGER.debug("Recently triggered: %s", str(TRIGGERED))

    while glob.glob(f'/var/run/{config.main.base_env}-data-{INTERVAL}-*'):
        LOGGER.info("Waiting for initial data collection to complete for %s", INTERVAL)
        time.sleep(30)

    LOGGER.debug("Start of current loop")
    redis = Redis()
    if CHECK_REDIS_PAIR:
        redis4=Redis(db=CHECK_REDIS_PAIR)
        redis_pairs = [x.decode().split(':') for x in
                       redis4.conn.smembers(f'{INTERVAL}:{DIRECTION}')]

        dbase = Mysql(interval=INTERVAL)
        open_pairs = dbase.fetch_sql_data(f'select pair, comment, 999999 from trades where '
                                          f'`interval`="{INTERVAL}" and name="{config.main.name}" '
                                          f'and close_price is null', header=False)
        open_pairs = [tuple(x) for x in open_pairs]
        redis_pairs = [tuple(x) for x in redis_pairs]

        # check if pair to be analysed is already open

        for pair, reversal, expire in redis_pairs:
            if int(config.redis.redis_expiry_seconds) > 0 and \
                    int(time.time()) > (int(config.redis.redis_expiry_seconds)  + int(expire)):
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
            details = [[pair[0], "2020-01-01 00:00:00", "1", "reopen", "0", 'None']]
            if pair[1] != 'reversal':
                trade.close_trade(details)

    else:
        # not being fetched from redis db
        pairs = [(pair, 'normal', 999999) for pair in PAIRS]

    for pair, reversal, expire in pairs:
        analyse_pair(pair, reversal, expire, redis)
    LOGGER.debug("End of current loop")
    Path('/var/local/greencandle').touch()
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
        container_num = int(config.main.name[-1])
    except ValueError:
        container_num = 1

    name_lookup = [['distance', 'bb', 'bbperc_diff', 'bbperc_extreme'], # new
                   ['atrp_change'], # new
                   ['old_distance', 'old_bb', "old_bbperc_diff", "old_bbperc_extreme"], # old
                   [],
                   ['MACD_slowdown'], # current
                   ['MACD'] # new step2
                   ]
    for match in matches:
        match_names.append(name_lookup[container_num-1][match-1])
    return ','.join(match_names)

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

    LOGGER.debug("Analysing pair: %s", pair)
    try:
        result, _, current_time, current_price, match = \
                redis.get_rule_action(pair=pair, interval=INTERVAL)
        event = reversal

        if result in ('OPEN', 'CLOSE'):
            LOGGER.info("Trades to %s for pair %s", result.lower(), pair)
            now = datetime.now()
            items = redis.get_items(pair, INTERVAL)
            data = redis.get_item(f"{pair}:{INTERVAL}", items[-1]).decode()
            redis3 = Redis(db=3)
            raw_agg = redis3.conn.hgetall(f"{pair}:{INTERVAL}")
            agg = {k.decode():v.decode() for k,v in raw_agg.items()}
            del redis3

            # Only alert on a given pair once per hour
            # for each strategy
            if pair in TRIGGERED:
                diff = now - TRIGGERED[pair]
                diff_in_hours = diff.total_seconds() / 3600
                if str2bool(config.main.wait_between_trades) and diff.total_seconds() < \
                        convert_to_seconds(config.main.time_between_trades):
                    LOGGER.debug("Skipping notification for %s %s as recently triggered",
                                 pair, INTERVAL)
                    return
                LOGGER.debug("Triggering alert: last alert %s hours ago", diff_in_hours)

            TRIGGERED[pair] = now
            try:
                match_strs = get_match_name(match[result.lower()])
            except IndexError:
                match_strs = match[result.lower()]
            msg = (f"{result.lower()}, {match_strs}: {get_tv_link(pair, INTERVAL)} "
                   f"{INTERVAL} {config.main.name} ({supported.strip()}) - {current_time} "
                   f"Data: {data} Agg: {agg}")

            if result == 'OPEN':
                send_slack_message("notifications", msg, emoji=True,
                                   icon=f':{INTERVAL}-{DIRECTION}:')
            if 'NSCA' in os.environ:
                send_nsca(status=0, host_name='hp', service_name=config.main.name,
                          text_output="OK", remote_host='10.8.0.1')

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
                else:
                    LOGGER.info("not closing reversal trade for %s", pair)

            if CHECK_REDIS_PAIR and result=='OPEN':
                redis4 = Redis(db=CHECK_REDIS_PAIR)
                redis4.conn.srem(f'{INTERVAL}:{DIRECTION}', f'{pair}:{reversal}:{expire}')
                LOGGER.info("trade opening %s:%s:%s - removing from redis db:%s", pair, reversal,
                            expire, CHECK_REDIS_PAIR)
            if ROUTER_FORWARD:
                url = f"http://router:1080/{config.web.api_token}"
                forward_strategy = config.web.forward
                payload = {"pair": pair,
                           "text": f"forwarding {result.lower()} trade from {config.main.name}",
                           "action": str(action),
                           "env": config.main.name,
                           "price": current_price,
                           "strategy": forward_strategy}

                try:
                    requests.post(url, json.dumps(payload), timeout=10,
                                  headers={'Content-Type': 'application/json'})
                    LOGGER.info("forwarding %s %s/%s trade to: %s match:%s",
                                pair, INTERVAL, DIRECTION,
                                forward_strategy, match_strs)

                except requests.exceptions.RequestException:
                    pass

            if REDIS_FORWARD:
                for forward_db in REDIS_FORWARD:
                    redis4 = Redis(db=forward_db)
                    # add to redis set
                    LOGGER.info("new forward trade adding %s to %s:%s set db %s",
                                pair, INTERVAL, DIRECTION, forward_db)
                    redis_pairs = [x.decode().split(':') for x
                                   in redis4.conn.smembers(f'{INTERVAL}:{DIRECTION}')]

                    # check pair doesn't already exist
                    if not [el for el in redis_pairs if el[0] == pair and el[1] == 'normal']:
                        now = int(time.time())
                        redis4.conn.sadd(f'{INTERVAL}:{DIRECTION}', f'{pair}:normal:{now}')
                    del redis4

            LOGGER.info("Trade alert: %s %s %s %s (%s)",result, pair, INTERVAL,
                        DIRECTION, supported.strip())
    except Exception as err_msg:
        LOGGER.critical("Error with pair %s %s", pair, str(err_msg))

@arg_decorator
def main():
    """
    Analyse data from redis and alert to slack if there are current trade opportunities
    Required: CONFIG_ENV var and config

    Usage: analyse_data
    """
    fwd_str = "-forward" if ROUTER_FORWARD else ''
    container_no = config.main.name[-1]

    setproctitle.setproctitle(f"analyse_data{container_no}-{INTERVAL}{fwd_str}")

    while True:
        analyse_loop()

if __name__ == "__main__":
    main()
