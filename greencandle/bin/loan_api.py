#!/usr/bin/env python
#pylint: disable=no-member

"""
API for tracking which pairs aren't tradable overtime
"""
import sys
from flask import Flask, request, Response
from setproctitle import setproctitle
from greencandle.lib import config
from greencandle.lib.common import arg_decorator
from greencandle.lib.logger import get_logger

config.create_config()
TEST = bool(len(sys.argv) > 1 and sys.argv[1] == '--test')
APP = Flask(__name__)
LOGGER = get_logger(__name__)

@APP.route('/webhook', methods=['POST'])
def respond():
    """
    Default route to trade
    """
    print(request.json)
    return Response(status=200)

@APP.route('/healthcheck', methods=["GET"])
def healthcheck():
    """
    Docker healthcheck
    Return 200
    """
    return Response(status=200)

@arg_decorator
def main():
    """
    Receives trade requests from web front-end/API/router and
    fetching maximum loanable amount
    """
    setproctitle(f"{config.main.base_env}-amount_api")
    APP.run(debug=False, host='0.0.0.0', port=20000, threaded=True)

if __name__ == "__main__":
    main()
