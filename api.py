#!/usr/bin/env python
#pylint: disable=broad-except,global-statement,too-few-public-methods

"""
API for binance/coinbase crypto data
"""

import calendar
import sched
import sys
import json
import threading
import time
from flask import Flask
import balance
import klines

DATA = None
BALANCE = None
SCHED = sched.scheduler(time.time, time.sleep)
DATA_TIMER = 60
BALANCE_TIMER = 300

class Namespace(object):
    """Namespace object for passing args(argparse) options"""
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

APP = Flask(__name__)
@APP.route('/data', methods=['GET'])
def get_analysis():
    """return html data"""
    return str(DATA)

@APP.route('/balance', methods=['GET'])
def fetch_balance():
    """return balance JSON"""
    return str(BALANCE)

def get_balance():
    """fetch balances and store in global variable"""
    balances = balance.get_binance_values()
    return json.dumps(balances)


def get_data():
    """Fetch data - called by scheduler periodically """

    pairs = ["XRPBTC", "XRPETH", "MANABTC", "PPTBTC", "MTHBTC", "BNBBTC", "BNBETH", "ETHBTC"]
    args = Namespace(graph=False)

    event_data = klines.get_details(pairs, args)
    eventsObj = klines.Events(event_data)
    eventsObj.get_data(pairs)
    events = eventsObj
    js = {}
    js["stories"] = {}
    js["events"] = events
    js["stories"]["time"] = calendar.timegm(time.gmtime())
    js["stories"]["type"] = "finish"
    js["stories"]["events"] = events.keys()
    return json.dumps(js)

def schedule_data(scheduler):
    """
    Scheduler function for fetching data hourly
    Runs in a background thread to not interfere with flask
    """

    global DATA
    try:
        DATA = get_data()
        sys.stdout.write("Successfully fetched data\n")

    except Exception as error:
        sys.stderr.write("Error opening URL\n" + str(error))

    SCHED.enter(DATA_TIMER, 1, schedule_data, (scheduler,))

def schedule_balance(scheduler):
    """get balance"""
    global BALANCE
    try:
        BALANCE = get_balance()
        sys.stdout.write("Successfully fetched balance\n")
    except Exception as error:
        sys.stderr.write("Error opening URL\n" + str(error))

    SCHED.enter(BALANCE_TIMER, 1, schedule_balance, (scheduler,))


def main():
    """Start Scheduler & flask app """

    SCHED.enter(0, 1, schedule_data, (SCHED,))
    SCHED.enter(0, 1, schedule_balance, (SCHED,))
    background_thread = threading.Thread(target=SCHED.run, args=())
    background_thread.daemon = True
    try:
        print "Loading scheduler"
        background_thread.start()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(1)
    APP.run(debug=True, threaded=True, port=5001, use_reloader=False)

if __name__ == '__main__':
    main()
