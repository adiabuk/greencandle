#!/usr/bin/env python
#pylint: disable=no-member,eval-used,unused-variable

"""
Loop through extra trade rules in redis and process
"""

import time
import json
import requests

from greencandle.lib import config
from greencandle.lib.redis_conn import Redis, get_float
from greencandle.lib.common import AttributeDict, arg_decorator

@arg_decorator
def main():
    """
    Retrieve extra trade rules from redis db6 and process
    run in loop every 5 secs
    """
    while True:
        check_rules()
        time.sleep(5)

def check_rules():
    """
    Loop through available rules
    """

    config.create_config()
    redis = Redis()
    redis3 = Redis(db=3)
    redis6 = Redis(db=6)

    # pair, interval, action, rule, forward_to

    items = []

    keys = redis6.conn.keys()
    for key in keys:
        items.append(list(json.loads(redis6.conn.get(key).decode()).values()))


    for pair, interval, action, rule, forward_to in items:
        if pair not in config.main.pairs.split():
            continue
        item = redis.get_items(pair, interval)[-1]
        res = []
        raw = redis3.conn.hgetall(f'{pair}:{interval}')
        agg = AttributeDict({k.decode():get_float(v.decode()) for k, v in raw.items()})
        name = f"{pair}:{interval}"
        # loop backwards through last 5 items
        ind_list = []
        for i in config.main.indicators.split():
            split = i.split(';')
            ind = split[1]+'_' +split[2].split(',')[0]
            ind_list.append(ind)

        try:
            items = redis.get_items(pair=pair, interval=interval)
            _ = items[-5]
        except (ValueError, IndexError) as err:
            print("Not enough data for %s: %s", pair, err)
            print('HOLD', 'Not enough data', 0, 0, {'open':[], 'close':[]})

        for i in range(-1, -6, -1):
            datax = AttributeDict()
            for indicator in ind_list:
                datax[indicator] = redis.get_result(items[i], indicator, pair, interval)

            # Floatify each of the ohlc elements before adding
            ohlc = redis.get_current(name, items[i])[-1]
            for item in ['open', 'high', 'low', 'close']:
                ohlc[item] = float(ohlc[item])

            datax.update(ohlc)
            res.append(datax)
        ###
        if eval(rule):
            print(pair, interval)
            url = f"http://router:1080/{config.web.api_token}"
            payload = {"pair": pair,
                       "text": f"forwarding {action.lower()} trade from extras dashboard",
                       "action": str(action),
                       "env": config.main.name,
                       "price": -1,
                       "strategy": forward_to}

            try:
                requests.post(url, json.dumps(payload), timeout=10,
                              headers={'Content-Type': 'application/json'})
                print(f"forwarding {pair} {interval} trade to: {forward_to}")
                redis6.conn.delete(f'{pair}:{interval}')

            except requests.exceptions.RequestException:
                pass

        else:
            print("no")

if __name__ == '__main__':
    main()
