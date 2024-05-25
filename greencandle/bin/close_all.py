#pylint: disable=no-member,too-many-locals
"""
Close all trades
"""
import json
import argparse
import argcomplete
import requests
from greencandle.lib.mysql import Mysql
from greencandle.lib.common import get_short_name, perc_diff
from greencandle.lib import config

def main():
    """
    Close all trades in current environment if perc is higher than threshold
    Threshold is 0.3 if no threshold supplied
    Usage close_all <net_perc>
    """
    parser = argparse.ArgumentParser("Close trades in scope")
    parser.add_argument("-f", "--name_filter", required=False, default="")
    parser.add_argument("-t", "--threshold", required=False, default=0.3)
    argcomplete.autocomplete(parser)
    args = parser.parse_args()

    config.create_config()
    env = config.main.base_env
    url = f"http://router:1080/{config.web.api_token}"
    dbase = Mysql()
    open_trades = dbase.get_open_trades(name_filter=args.name_filter)
    stream_req = requests.get('http://stream/1m/all', timeout=10)
    prices = stream_req.json()

    for trade in open_trades:
        open_time, _, pair, name, open_price, direction, _ = trade
        current_price = prices['recent'][pair]['close']
        perc = perc_diff(open_price, current_price)
        perc = -perc if direction== 'short' else perc

        if float(perc) > float(args.threshold):
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
