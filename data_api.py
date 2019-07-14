#return !/usr/bin/env python
#pylint: disable=global-statement

"""
API for binance crypto data
"""

from __future__ import print_function
import sched
import sys
import json
import threading
from time import time, strftime, sleep, gmtime
from collections import defaultdict
from flask import Flask, abort
from lib.config import get_config
from lib.scrape import scrape_data

PAIRS = get_config("api")["pairs"].split()
INTERVAL = get_config("api")["interval"]
PORT = int(get_config("api")["port"])

DATA = defaultdict(defaultdict)

SCHED = sched.scheduler(time, sleep)
DATA_TIMER = 240  # Every 4 mins

APP = Flask(__name__)

def schedule_data(scheduler):
    """
    Scheduler function for fetching data hourly
    Runs in a background thread to not interfere with flask
    """

    global DATA
    try:
        print(strftime("%Y-%m-%d %H:%M:%S", gmtime()), "Fetching data\n")
        data = get_data()
        for key, value in json.loads(data.replace("\'", "\"")).items():

            # Backup previous value and store new one
            DATA[key]["previous"] = DATA[key]["current"]
            DATA[key]["current"] = value
            DATA[key]["uptate"] = strftime("%Y-%m-%d %H:%M:%S", gmtime())

        print(strftime("%Y-%m-%d %H:%M:%S", gmtime()), "Successfully fetched data\n")

    except TypeError as error:
        sys.stderr.write("Error opening URL\n" + str(error))


    SCHED.enter(DATA_TIMER, 1, schedule_data, (scheduler,))
@APP.route("/data", methods=["GET"])
def get_events():
    """return event data"""
    if not DATA:
        abort(500, json.dumps({"response": "Data not yet populated, try again later"}))

    return json.dumps(DATA)

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
