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
from time import time, strftime, gmtime, sleep
from flask import Flask, abort
import balance
import backend
import binance

PAIRS = [price for price in binance.prices().keys() if price != '123456']

DATA = None
HOLD = None
ALL_DATA = None
BALANCE = None

SCHED = sched.scheduler(time, sleep)
DATA_TIMER = 60
BALANCE_TIMER = 300

APP = Flask(__name__)

@APP.route('/all', methods=['GET'])
def get_all_data():
    """ Return all data: HOLD, and EVENT """
    return str(ALL_DATA)

@APP.route('/data', methods=['GET'])
def get_events():
    """return event data"""
    if not DATA:
        abort(500, json.dumps({'response': 'Data not yet populated, try again later'}))

    return str(DATA)

@APP.route('/hold', methods=['GET'])
def get_hold():
    """get hold events"""
    if not HOLD:
        abort(500, json.dumps({'response': 'Data not yet populated, try again later'}))

    return str(HOLD)

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

    events = backend.Events(PAIRS)
    events.get_data()
    data = {}
    hold = {}
    data["stories"] = {}
    hold["stories"] = {}
    data["events"] = events['event']
    hold["events"] = events['hold']
    data["stories"]["time"] = calendar.timegm(gmtime())
    hold["stories"]["time"] = calendar.timegm(gmtime())
    data["stories"]["type"] = "finish"
    hold["stories"]["type"] = "finish"
    data["stories"]["events"] = list(events["event"].keys())
    hold["stories"]["events"] = list(events["hold"].keys())
    if not hold["stories"]["events"]:
        print("FAILED to fetch data")
    return json.dumps(data), json.dumps(hold)

def schedule_data(scheduler):
    """
    Scheduler function for fetching data hourly
    Runs in a background thread to not interfere with flask
    """

    global DATA, HOLD
    try:
        print(strftime("%Y-%m-%d %H:%M:%S", gmtime()), "Fetching data\n")
        DATA, HOLD = get_data()
        print(strftime("%Y-%m-%d %H:%M:%S", gmtime()), "Successfully fetched data\n")

    except TypeError as error:
        sys.stderr.write("Error opening URL: " + str(error) + "\n")

    SCHED.enter(DATA_TIMER, 1, schedule_data, (scheduler,))

def schedule_balance(scheduler):
    """get balance"""
    global BALANCE
    try:
        sys.stdout.write('hello')
        print(strftime("%Y-%m-%d %H:%M:%S", gmtime()), "Fetching balance\n")
        BALANCE = get_balance()
        print(strftime("%Y-%m-%d %H:%M:%S", gmtime()), "Successfully fetched balance\n")
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
