#!/usr/bin/env python

#pylint: disable=no-member,no-name-in-module,broad-except

"""
API for tracking which pairs aren't tradable overtime
"""
import logging
from flask import Flask, request, Response
from setproctitle import setproctitle
from greencandle.lib import config
from greencandle.lib.common import arg_decorator, format_usd
from greencandle.lib.logger import get_logger
from greencandle.lib.balance_common import get_quote, get_base
from greencandle.lib.binance_accounts import base2quote
from greencandle.lib.auth import binance_auth
from greencandle.lib.binance import BinanceException

config.create_config()
APP = Flask('loan_api')
LOGGER = get_logger('loan_api')

@APP.route('/webhook', methods=['POST', 'GET'])
def respond():
    """
    Default route to trade
    """
    #if request.method == 'GET':

    data = request.json if request.method == 'POST' else request.args
    keys = ['pair', 'action']
    if not all(key in data.keys() for key in keys):
        response = f'Missing keys, provided: {str(data.keys())}, required: {str(keys)}'
        LOGGER.warning(response)
        return Response(response=response + '\n', status=500)

    client = binance_auth()
    if int(data['action']) == -1:
        asset = get_base(data['pair'].upper())
        direction = "short"
    elif int(data['action']) == 1:
        asset = get_quote(data['pair'].upper())
        direction = "long"

    LOGGER.debug("Request received: %s", str(data))

    try:
        max_usd_only_borrow = client.get_max_borrow(asset='USDT')
        max_borrow = client.get_max_borrow(asset=asset)
        max_usd_borrow = max_borrow if 'USD' in asset else base2quote(max_borrow, asset+'USDT')
    except BinanceException:
        max_borrow = 0
        max_usd_borrow = 0
        LOGGER.warning("Binance excption - no funds available")
    origin = data['text'].split()[-3] if "text" in data else "unknown"

    ret_str = (f"Max borrow amount for {data['pair']} {direction} is "
               f"{format_usd(max_usd_borrow)},usd borrow:{format_usd(max_usd_only_borrow)},"
               f"{origin}")
    LOGGER.info(ret_str)
    return ret_str + '\n'

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
    setproctitle(f"{config.main.base_env}-loan_api")
    logging.basicConfig(level=logging.ERROR)
    if float(config.main.logging_level) > 10:
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        log.disabled = True
    APP.run(debug=False, host='0.0.0.0', port=20000, threaded=True)

if __name__ == "__main__":
    main()
