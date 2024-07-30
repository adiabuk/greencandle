#!/usr/bin/env python
#pylint: disable=no-member,eval-used,unused-variable,broad-except

"""
Loop through extra trade rules in redis and process
"""

import time
import json
import requests
from send_nsca3 import send_nsca
from greencandle.lib import config
from greencandle.lib.redis_conn import Redis, get_float
from greencandle.lib.common import AttributeDict, arg_decorator
from greencandle.lib.logger import get_logger

LOGGER = get_logger(__name__)

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
    redis = Redis() # ohlc
    redis3 = Redis(db=3) # agg
    redis6 = Redis(db=12) # current rules
    redis11 = Redis(db=11) # processed rules

    items = []

    keys = redis6.conn.keys()
    for key in keys:
        items.append(list(json.loads(redis6.conn.get(key).decode()).values()) + [key.decode()])


    for pair, interval, action, usd, take, stop, rule, forward_to, key in items:
        if pair not in config.main.pairs.split():
            msg = f'Unknown pair: {pair}'
            LOGGER.info(msg)
            send_nsca(status=2, host_name='jenkins1', service_name='extra_rules', text_output=msg,
                      remote_host='local.amrox.loc')
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
            print("Not enough data  for %s: %s", pair, err)
            print('HOLD', 'Not enough data', 0, 0, {'open':[], 'close':[]})

        for i in range(-1, -6, -1):
            datax = AttributeDict()
            for indicator in ind_list:
                datax[indicator] = redis.get_result(items[i], indicator, pair, interval)

            # Floatify each of the ohlc elements before adding
            ohlc = redis.get_current(name, items[i])[-1]
            for item in ['open', 'high', 'low', 'close']:
                ohlc[item] = float(ohlc[item])
            ha_raw = redis.get_current(name, items[i], 'HA_0')[-1]
            if ha_raw:
                ha_ohlc={}
                for item in ['open', 'high', 'low', 'close']:
                    ha_ohlc[f'HA_{item}'] = float(ha_raw[item])
                datax.update(ha_ohlc)


            datax.update(ohlc)
            res.append(datax)
        ###
        try:
            evalled = eval(rule)
        except Exception as err:
            msg = f"Unable to eval rule {str(rule)} for {pair} {interval}"
            LOGGER.info(msg)
            send_nsca(status=2, host_name='jenkins1', service_name='extra_rules', text_output=msg,
                      remote_host='local.amrox.loc')
            continue
        if evalled:
            print(pair, interval)
            url = f"http://router:1080/{config.web.api_token}"
            payload = {"pair": pair,
                       "text": f"forwarding {action.lower()} trade from extras dashboard",
                       "action": str(action),
                       "env": config.main.name,
                       "price": -1,
                       "usd": usd,
                       "tp": take,
                       "sl": stop,
                       "strategy": forward_to}

            try:
                requests.post(url, json.dumps(payload), timeout=10,
                              headers={'Content-Type': 'application/json'})

                LOGGER.info("TRADE: forwarding %s %s trade to: %s - rule: %s",
                            pair, interval, forward_to, rule)

                data = {"pair":pair, "interval": interval, "action": action, "usd": usd,
                        "take": take, "stop": stop, "rule": rule, "forward_to": forward_to}

                redis11.conn.set(f"{str(int(time.time()))}", json.dumps(data))
                redis6.conn.delete(key)


            except requests.exceptions.RequestException:
                pass

if __name__ == '__main__':
    main()
