#!/usr/bin/env python
# pylint: disable=global-statement,wrong-import-position,too-few-public-methods, no-else-return

"""
API dashboard
"""

from __future__ import print_function
import threading
import sched
import sys
import glob
import os
from time import time, sleep, strftime, gmtime
from pathlib import Path
from flask import Flask, render_template, request

from waitress import serve
from greencandle.lib import config
config.create_config()
from greencandle.lib.order import Trade
from greencandle.lib.mysql import Mysql

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
APP.wsgi_app = PrefixMiddleware(APP.wsgi_app, prefix='/api')

SCHED = sched.scheduler(time, sleep)
DATA = {}
TEST = None

@APP.route('/')
def trades():
    """deployments page"""
    return render_template('trades.html', versions=DATA)

@APP.route('/sell', methods=["GET", "POST"])
def sell():
    """sell a given trade"""

    global TEST
    print("SELL", file=sys.stderr)
    pair = request.args.get('pair')
    name = request.args.get('name')
    current_price = request.args.get('price')
    print(pair, name, file=sys.stderr)

    test_trade = bool(os.environ['HOST'] in ["test", "stag"])
    trade = Trade(interval='4h', test_data=TEST, test_trade=test_trade)

    current_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    sells = [(pair, current_time, current_price)]

    # Sell, then update page
    trade.sell(sells, name=name)
    sleep(1)
    get_data(SCHED)
    return trades()

def healthcheck(scheduler):
    """Healtcheck for docker"""
    Path('/var/run/greencandle').touch()
    SCHED.enter(60, 60, healthcheck, (scheduler, ))

def get_data(scheduler):
    """get data from mysql"""
    global DATA
    print("Getting version data", file=sys.stderr)
    DATA = {}
    dbase = Mysql()

    results = dbase.fetch_sql_data("select * from open_trades", header=False)

    for entry in results:
        pair, buy_price, buy_time, current_price, perc, name = entry
        print(entry, file=sys.stdout)
        list_of_files = glob.glob('/data/graphs/{}*'.format(pair))
        try:
            # strip path from filename
            latest_file = max(list_of_files, key=os.path.getctime).split('/')[-1]
        except ValueError: # no files
            latest_file = ""

        DATA[pair] = {"buy_price": buy_price, "buy_time": buy_time,
                      "current_price": current_price, "perc": perc,
                      "graph": latest_file, "name": name}

    SCHED.enter(60, 60, get_data, (scheduler, ))

def main():
    """main func"""

    global TEST
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("API for interacting with trading system")
        sys.exit(0)
    TEST = bool(len(sys.argv) > 1 and sys.argv[1] == '--test')

    SCHED.enter(0, 60, get_data, (SCHED,))
    SCHED.enter(0, 60, healthcheck, (SCHED,))

    background_thread = threading.Thread(target=SCHED.run, args=())
    background_thread.daemon = True
    background_thread.start()

    if TEST:
        print("test node")
        APP.run(debug=True, host='0.0.0.0', port=5000, threaded=True)
    else:
        serve(APP, host="0.0.0.0", port=5000)

if __name__ == '__main__':
    main()
