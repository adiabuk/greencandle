#!/usr/bin/env python
#pylint: disable=global-statement

"""
API for binance crypto data
"""

from __future__ import print_function
import sched
import sys
import os
import json
import threading
from time import time, strftime, sleep, gmtime
from flask import Flask, abort, send_file
from lib.config import get_config
from lib.scrape import scrape_data

PAIRS = get_config("api")["pairs"].split()
INTERVAL = get_config("api")["interval"]
PORT = int(get_config("api")["port"])

DATA = None

SCHED = sched.scheduler(time, sleep)
DATA_TIMER = 240  # Every 4 mins
BALANCE_TIMER = 300

APP = Flask(__name__)

@APP.route("/<path:path>", methods=["GET"])
def return_file(path):
    """Fetch generated PNG thumbnails """
    if path.startswith("graphs/in/") and path.endswith(".png") and os.path.isfile(path):
        return send_file(path, as_attachment=True)
    abort(404)
    return False

def schedule_data(scheduler):
    """
    Scheduler function for fetching data hourly
    Runs in a background thread to not interfere with flask
    """

    global DATA
    try:
        print(strftime("%Y-%m-%d %H:%M:%S", gmtime()), "Fetching data\n")
        DATA = get_data()
        print(strftime("%Y-%m-%d %H:%M:%S", gmtime()), "Successfully fetched data\n")

    except TypeError as error:
        sys.stderr.write("Error opening URL\n" + str(error))

    SCHED.enter(DATA_TIMER, 1, schedule_data, (scheduler,))

@APP.route("/data", methods=["GET"])
def get_events():
    """return event data"""
    if not DATA:
        abort(500, json.dumps({"response": "Data not yet populated, try again later"}))

    return str(DATA)

def get_data():
    """Fetch data - called by scheduler periodically """
    data = scrape_data("firefox")

    return json.dumps(data)

def main():
    """Start Scheduler & flask app """

    SCHED.enter(0, 1, schedule_data, (SCHED,))
    background_thread = threading.Thread(target=SCHED.run, args=())
    background_thread.daemon = True
    try:
        print("Loading scheduler")
        background_thread.start()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(1)
    APP.run(debug=True, threaded=True, port=PORT, use_reloader=False)

if __name__ == "__main__":
    main()
