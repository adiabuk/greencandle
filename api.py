#!/usr/bin/env python
#pylint: disable=broad-except,global-statement,too-few-public-methods

"""
API for binance/coinbase crypto data
"""

from __future__ import print_function
import calendar
import sched
import sys
import json
import threading
import time
from flask import Flask, abort
import balance
import klines

DATA = None
BALANCE = None
SCHED = sched.scheduler(time.time, time.sleep)
DATA_TIMER = 60
BALANCE_TIMER = 300

APP = Flask(__name__)

@APP.route('/data', methods=['GET'])
def get_analysis():
    """return html data"""
    if not DATA:
        abort(500, json.dumps({'response': 'Data not yet populated, try again later'}))

    return str(DATA)

@APP.route('/balance', methods=['GET'])
def fetch_balance():
    """return balance JSON"""
    return str(BALANCE)

def get_balance():
    """fetch balances and store in global variable"""
    balances = balance.get_balance()
    return json.dumps(balances)


def get_data():
    """Fetch data - called by scheduler periodically """

    pairs = ["XRPBTC", "XRPETH", "MANABTC", "PPTBTC", "MTHBTC", "BNBBTC", "BNBETH", "ETHBTC"]

    event_data = klines.get_details(pairs)
    events = klines.Events(event_data)
    events.get_data(pairs)
    all_data = {}
    all_data["stories"] = {}
    all_data["events"] = events
    all_data["stories"]["time"] = calendar.timegm(time.gmtime())
    all_data["stories"]["type"] = "finish"
    all_data["stories"]["events"] = events.keys()
    return json.dumps(all_data)

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
        print("Loading scheduler")
        background_thread.start()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(1)
    APP.run(debug=True, threaded=True, port=5001, use_reloader=False)

if __name__ == '__main__':
    main()
