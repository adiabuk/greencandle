#!/usr/bin/env python
#pylint: disable=no-member

"""
API for tracking which pairs aren't tradable overtime
"""
from flask import Flask, request, Response
from setproctitle import setproctitle
from greencandle.lib import config
from greencandle.lib.common import arg_decorator
from greencandle.lib.logger import get_logger
from greencandle.lib.balance_common import get_quote, get_base
from greencandle.lib.binance_accounts import base2quote
from greencandle.lib.auth import binance_auth
from greencandle.lib.binance import BinanceException

config.create_config()
APP = Flask(__name__)
LOGGER = get_logger(__name__)

@APP.route('/webhook', methods=['POST'])
def respond():
    """
    Default route to trade
    """
    try:
        data = request.json
        client = binance_auth()
        if int(data['action']) == -1:
            asset = get_base(data['pair'].upper())
            direction = "short"
        elif int(data['action']) == 1:
            asset = get_quote(data['pair'].upper())
            direction = "long"
        else:
            return Response(status=200)

        LOGGER.info("Request received: %s", str(data))

        try:
            max_usd_only_borrow = client.get_max_borrow(asset='USDT')
            max_borrow = client.get_max_borrow(asset=asset)
            max_usd_borrow = max_borrow if 'USD' in asset else base2quote(max_borrow, asset+'USDT')
        except BinanceException:
            max_borrow = 0
            max_usd_borrow = 0
            LOGGER.warning("Binance excption - no funds available")
        LOGGER.info("Borrow amount for %s %s is %s %s (%s USD), usd_only:%s, %s", data['pair'],
                    direction, max_borrow, asset, max_usd_borrow, max_usd_only_borrow,
                    data['strategy'])
    except Exception as err:
        LOGGER.warning("Error: %s", str(err))

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
