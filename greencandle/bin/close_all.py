#pylint: disable=no-member
"""
Close all trades
"""
import sys
import json
import requests
from greencandle.lib.mysql import Mysql
from greencandle.lib.common import get_short_name, arg_decorator
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
    dbase.get_active_trades()
    open_trades = dbase.fetch_sql_data('select pair, name, net_perc, direction from open_trades',
                                       header=False)

    for trade in open_trades:
        pair, name, net_perc, direction = trade
        if float(net_perc) > (float(sys.argv[1]) if len(sys.argv) > 1 else 0.3):
            short_name = get_short_name(name, env, direction)
            print(f"We can close {pair} {name} {direction} @ {net_perc}%")
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
