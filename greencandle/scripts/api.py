#!/usr/bin/env python
#pylint: disable=global-statement,wrong-import-position,too-few-public-methods,
#pylint: disable=invalid-name,no-member,no-else-return

"""
API dashboard
"""

from __future__ import print_function
import threading
import sched
import sys
import glob
import os
from importlib import reload
from time import time, sleep, strftime, gmtime
from pathlib import Path
from flask import Flask, render_template, request, redirect

from waitress import serve
from greencandle.lib import config
config.create_config()
from greencandle.lib.logger import get_logger
from greencandle.lib.order import Trade
import greencandle.lib.redis_conn as redis_conn
from greencandle.lib.mysql import Mysql
from greencandle.lib.binance_common import get_current_price

class PrefixMiddleware():
    """ API prefix handler """
    def __init__(self, app, prefix=''):
        self.app = app
        self.prefix = prefix

    def __call__(self, environ, start_response):
        print(self.prefix, environ['PATH_INFO'], file=sys.stderr)
        if environ['PATH_INFO'].startswith(self.prefix):
            environ['PATH_INFO'] = environ['PATH_INFO'][len(self.prefix):]
            environ['SCRIPT_NAME'] = self.prefix
            return self.app(environ, start_response)
        else:
            start_response('404', [('Content-Type', 'text/plain')])
            return ["This url does not belong to the app.".encode()]

APP = Flask(__name__, template_folder="/etc/gcapi", static_url_path='/etc/gcapi/',
            static_folder='/etc/gcapi')
LOGGER = get_logger(__name__)
HANDLER = LOGGER.handlers[0]
APP.logger.addHandler(HANDLER)
APP.wsgi_app = PrefixMiddleware(APP.wsgi_app, prefix='/api')

SCHED = sched.scheduler(time, sleep)
DATA = {}
RULES = []
ALL = {}
TEST = None

@APP.route('/')
def trades():
    """deployments page"""
    return render_template('trades.html', versions=DATA, all=ALL, rules=RULES)

@APP.route('/sell', methods=["GET", "POST"])
def sell():
    """sell a given trade"""

    global TEST
    print("SELL", file=sys.stderr)
    pair = request.args.get('pair')
    name = config.main.name
    current_price = request.args.get('price')
    print(pair, name, file=sys.stderr)

    test_trade = bool(os.environ['HOST'] in ["test", "stag"])
    trade = Trade(interval='4h', test_data=TEST, test_trade=test_trade)

    current_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    sells = [(pair, current_time, current_price)]

    # Sell, then update page
    trade.sell(sells, name=name)
    sleep(1)
    dbase = Mysql(interval='4h', test=test_trade)
    dbase.get_active_trades()
    del dbase
    get_open(SCHED)
    get_closed(SCHED)
    return redirect("/api", code=302)

@APP.route('/buy', methods=["GET", "POST"])
def buy():
    """Buy a given pair"""
    global TEST
    print("BUY", file=sys.stderr)
    pair = request.args.get('pair')
    test_trade = bool(os.environ['HOST'] in ["test", "stag"])
    trade = Trade(interval='4h', test_data=TEST, test_trade=test_trade)
    current_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    current_price = get_current_price(pair)
    buys = [(pair, current_time, current_price)]
    trade.buy(buys)
    sleep(1)
    dbase = Mysql()
    dbase.get_active_trades()
    del dbase
    get_open(SCHED)
    get_closed(SCHED)
    return redirect("/api", code=302)


def healthcheck(scheduler):
    """Healtcheck for docker"""
    Path('/var/run/api').touch()
    SCHED.enter(60, 60, healthcheck, (scheduler, ))

def get_open(scheduler):
    """get open trades from mysql"""
    global DATA
    local_data = {}
    print("Getting open trades", file=sys.stderr)
    DATA = {}
    dbase = Mysql()
    interval = '4h'
    results = dbase.fetch_sql_data("select * from open_trades", header=False)

    redis = redis_conn.Redis(interval=interval, test=False, db=0)
    for entry in results:
        pair, buy_price, buy_time, current_price, perc, name = entry
        matching = redis.get_action(pair=pair, interval=interval)[-1]
        print(entry, file=sys.stdout)

        local_data[pair] = {"buy_price": buy_price, "buy_time": buy_time,
                            "matching": "Buy:{},Sell:{}".format(matching["buy"], matching["sell"]),
                            "current_price": current_price, "perc": perc,
                            "graph": get_latest_graph(pair, "html"), "name": name,
                            "strategy": get_keys_by_value(config.pairs, pair),
                            "thumbnail": get_latest_graph(pair, "resized.png")}
    DATA = local_data
    del redis
    SCHED.enter(60, 60, get_open, (scheduler, ))

def get_keys_by_value(dict_of_elements, value_to_find):
    """
    get dict key containing a given value
    """
    list_of_items = dict_of_elements.items()
    for item in list_of_items:
        if  value_to_find in item[1]:
            return item[0]
    return "Unknown"

def get_rules():
    """
    Get buy and sell rules from config
    """
    global RULES
    RULES = {}

    for rule in "buy", "sell":
        for seq in range(1, 10):
            try:
                RULES["{}_{}".format(rule, seq)] = config.main["{}_rule{}".format(rule, seq)]
            except KeyError:
                pass

def get_closed(scheduler):
    """
    get details of closed pairs
    """
    global ALL
    global config
    local_all = {}
    print("Getting all pairs", file=sys.stderr)
    pairs = [pair for pair in config.main.pairs.split() if pair not in DATA.keys()]
    for pair in pairs:
        interval = '4h'
        print("Getting pair", pair, file=sys.stderr)
        try:
            config.main.rate_indicator = 'EMA_2'
            reload(redis_conn)
            redis = redis_conn.Redis(interval=interval, test=False, db=0)
            matching = redis.get_action(pair=pair, interval=interval)[-1]
            del redis
        except (TypeError, KeyError):
            config.main.rate_indicator = 'EMA_8'
            reload(redis_conn)
            redis = redis_conn.Redis(interval=interval, test=False, db=0)
            matching = redis.get_action(pair=pair, interval=interval)[-1]
            del redis

        local_all[pair] = {"matching": "Buy:{},Sell:{}".format(matching["buy"], matching["sell"]),
                           "graph": get_latest_graph(pair, "html"),
                           "strategy": get_keys_by_value(config.pairs, pair),
                           "thumbnail": get_latest_graph(pair, "resized.png")}
    ALL = local_all
    SCHED.enter(600, 600, get_closed, (scheduler, ))

def get_latest_graph(pair, suffix=''):
    """
    return path of latest graph for a given pair
    """

    list_of_files = glob.glob('/data/graphs/{}*{}'.format(pair, suffix))
    try:
        # strip path from filename
        latest_file = max(list_of_files, key=os.path.getctime).split('/')[-1]
    except ValueError: # no files
        latest_file = ""
    return latest_file

def main():
    """main func"""

    global TEST
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("API for interacting with trading system")
        sys.exit(0)
    TEST = bool(len(sys.argv) > 1 and sys.argv[1] == '--test')

    SCHED.enter(0, 60, get_open, (SCHED,))
    SCHED.enter(0, 600, get_closed, (SCHED,))
    SCHED.enter(0, 60, healthcheck, (SCHED,))

    background_thread = threading.Thread(target=SCHED.run, args=())
    background_thread.daemon = True
    background_thread.start()
    get_rules()
    if TEST:
        print("test node")
        APP.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
    else:
        serve(APP, host="0.0.0.0", port=5000)

if __name__ == '__main__':
    main()
