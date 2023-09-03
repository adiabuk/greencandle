#pylint: disable=no-member
"""
Close all trades
"""
import os
import sys
import json
import requests
from greencandle.lib.mysql import Mysql
from greencandle.lib.common import get_short_name, arg_decorator, perc_diff
from greencandle.lib import config

@arg_decorator
def main():
    """
    Close all trades in current environment if net_perc is higher than arg
    Threshold is 0.3 if no arg supplied
    Usage close_all <net_perc>
    """
    config.create_config()
    env = config.main.base_env
    url = f"http://router:1080/{config.web.api_token}"
    dbase = Mysql()
    open_trades = dbase.get_open_trades()
    stream = os.environ['STREAM']
    stream_req = requests.get(stream, timeout=10)
    prices = stream_req.json()

    for trade in open_trades:
        open_time, _, pair, name, open_price, direction = trade
        current_price = prices['recent'][pair]['close']
        perc = perc_diff(open_price, current_price)
        perc = -perc if direction== 'short' else perc

        if float(perc) > (float(sys.argv[1]) if len(sys.argv) > 1 else 0.3):
            short_name = get_short_name(name, env, direction)
            print(f"Closing {pair} {name} {direction} from {open_time} @ {perc}%")
            payload = {"pair": pair,
                       "text": "closing trade from close_all script",
                       "action": "close",
                       "host": env,
                       "env": env,
                       "strategy": short_name}

            requests.post(url, json.dumps(payload), timeout=10,
                          headers={'Content-Type': 'application/json'})

if __name__ == "__main__":
    main()
