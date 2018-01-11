#!/usr/bin/env python

"""
Periodically fetch Emacs org-mode data from git and serve aggregated results as html on port 5000
"""


import sched
import sys
import threading
import time
from flask import Flask
import klines

DATA = None
SCHED = sched.scheduler(time.time, time.sleep)
TIMER = 1

class Namespace:
    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)

APP = Flask(__name__)
@APP.route('/data', methods=['GET'])
def hello_world():
    """return html data"""
    global DATA
    sys.stderr.write('Hello world! ')
    sys.stderr.write(str(type(DATA)))

    return str(DATA)

def get_data():
    """Fetch data - called by scheduler periodically """

    li = []
    args=None
    pairs = ["XRPBTC", "XRPETH", "MANABTC", "PPTBTC", "MTHBTC", "BNBBTC", "BNBETH", "ETHBTC" ]
    args = Namespace(graph=False)

    event_data = klines.get_details(pairs, args)
    events = klines.Events(event_data)
    data = events.get_data(pairs)
    #sys.stderr.write(data)
    return data
    return events.get_json()

def schedule_data(scheduler):
    """
    Scheduler function for fetching data hourly
    Runs in a background thread to not interfere with flask
    """

    global DATA
    try:
        DATA = get_data()
        sys.stdout.write("Successfully fetched data\n")

    except Exception as e:
        sys.stderr.write("Error opening URL\n", e)

    SCHED.enter(TIMER, 1, schedule_data, (scheduler,))


def main():
    """Start Scheduler & flask app """

    SCHED.enter(0, 1, schedule_data, (SCHED,))
    background_thread = threading.Thread(target=SCHED.run, args=())
    background_thread.daemon = True
    try:
        background_thread.start()
    except (KeyboardInterrupt, SystemExit):
        sys.exit(1)
    APP.run(debug=True, threaded=True)

if __name__ == '__main__':
    main()
