#!/usr/bin/env python
#pylint: disable=global-statement,wrong-import-position,too-few-public-methods
#pylint: disable=invalid-name,no-member,no-else-return,logging-not-lazy

"""
API dashboard
"""

import sys
import glob
import os
from importlib import reload
from time import sleep, strftime, gmtime
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler
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

SCHED = BackgroundScheduler(daemon=True)
DATA = {}
RULES = []
ALL = {}
TEST = bool(len(sys.argv) > 1 and sys.argv[1] == '--test')
TEST_TRADE = not ('HOST' in os.environ and os.environ['HOST'] == "prod")

@APP.route('/')
def trades():
    """deployments page"""
    return render_template('trades.html', versions=DATA, all=ALL, rules=RULES,
                           test=TEST, test_trade=TEST_TRADE)

@APP.route('/sell', methods=["GET", "POST"])
def sell():
    """sell a given trade"""

    global TEST
    pair = request.args.get('pair')
    LOGGER.info("Selling pair %s" % pair)

    current_price = request.args.get('price')

    interval = DATA[pair]['interval']
    trade = Trade(interval=interval, test_data=TEST, test_trade=TEST_TRADE)

    current_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    sells = [(pair, current_time, current_price)]

    # Sell, then update page
    trade.close_trade(sells)
    sleep(1)
    dbase = Mysql(interval='4h', test=TEST_TRADE)
    dbase.get_active_trades()
    del dbase
    return redirect("/api", code=302)

@APP.route('/buy', methods=["GET", "POST"])
def buy():
    """Buy a given pair"""
    global TEST
    pair = request.args.get('pair')
    LOGGER.info("Buying pair %s" % pair)
    trade = Trade(interval='4h', test_data=TEST, test_trade=TEST_TRADE)
    current_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    current_price = get_current_price(pair)
    buys = [(pair, current_time, current_price)]
    trade.open_trade(buys)
    sleep(1)
    dbase = Mysql()
    dbase.get_active_trades()
    del dbase
    return redirect("/api", code=302)


def healthcheck():
    """Healtcheck for docker"""
    Path('/var/run/api').touch()

def get_open():
    """get open trades from mysql"""
    global DATA
    local_data = {}
    LOGGER.debug("Getting open trades")
    dbase = Mysql()
    results = dbase.fetch_sql_data("select * from open_trades", header=False)

    redis = redis_conn.Redis(interval='4h', test=False)
    for entry in results:
        pair, open_price, open_time, current_price, perc, interval, name = entry
        matching = redis.get_action(pair=pair, interval=interval)[-1]

        local_data[pair] = {"open_price": open_price, "open_time": open_time,
                            "matching": "Buy:{},Sell:{}".format(matching["buy"], matching["sell"]),
                            "current_price": current_price, "perc": perc, "interval": interval,
                            "graph": get_latest_graph(pair, "html"), "name": name,
                            "strategy": get_keys_by_value(config.pairs, pair),
                            "thumbnail": get_latest_graph(pair, "resized.png")}
        DATA[pair] = local_data[pair]

    DATA = local_data
    del redis

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

def get_closed():
    """
    get details of closed pairs
    """
    global ALL
    global config
    local_all = {}
    LOGGER.debug("Getting closed trades")
    pairs = []
    for values in config.pairs.values():
        for value in values.split():
            if value not in DATA.keys():
                pairs.append(value)

    for pair in pairs:
        config.main.rate_indicator = 'EMA_2'
        interval = '4h'
        reload(redis_conn)
        redis = redis_conn.Redis(interval=interval, test=False)
        matching = {'buy': 'N/A', 'sell': 'N/A'}
        del redis

        local_all[pair] = {"matching": "Buy:{},Sell:{}".format(matching["buy"], matching["sell"]),
                           "graph": get_latest_graph(pair, "html"),
                           "strategy": get_keys_by_value(config.pairs, pair),
                           "thumbnail": get_latest_graph(pair, "resized.png")}
        ALL[pair] = local_all[pair]
    ALL = local_all

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

    SCHED.add_job(get_open, 'interval', seconds=5)
    SCHED.add_job(get_closed, 'interval', seconds=60)
    SCHED.add_job(healthcheck, 'interval', seconds=60)
    SCHED.start()

    get_rules()
    if TEST:
        LOGGER.debug("API started in test mode")
        APP.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
    else:
        serve(APP, host="0.0.0.0", port=5000)

if __name__ == '__main__':
    main()
