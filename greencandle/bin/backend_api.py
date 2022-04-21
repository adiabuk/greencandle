#!/usr/bin/env python
#pylint: disable=wrong-import-position,no-member,logging-not-lazy

"""
API trading module
"""
import sys
from time import strftime, gmtime
from flask import Flask, request, Response
from greencandle.lib.common import arg_decorator
from greencandle.lib import config
config.create_config()
from greencandle.lib.binance_common import get_current_price
from greencandle.lib.logger import get_logger
from greencandle.lib.order import Trade

TEST = bool(len(sys.argv) > 1 and sys.argv[1] == '--test')
APP = Flask(__name__)
LOGGER = get_logger(__name__)

@APP.route('/webhook', methods=['POST'])
def respond():
    """
    Default route to trade
    """
    print("action:", request.json)
    pair = request.json['pair'].upper()
    action = request.json['action'].upper()
    text = request.json['text']
    LOGGER.info("Request received: %s %s %s" %(pair, action, text))
    current_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    current_price = get_current_price(pair)
    item = [(pair, current_time, current_price, config.main.name)]
    trade = Trade(interval=config.main.interval, test_data=False, test_trade=TEST, config=config)
    if action == 'OPEN':
        trade.open_trade(item)
    elif action == 'CLOSE':
        trade.close_trade(item, drawdowns={pair:0}, drawups={pair:0})

    return Response(status=200)

@arg_decorator
def main():
    """
    Receives trade requests from web front-end/API/router and
    open/close trade as appropriate
    
    Usage: backend_api
    """

    APP.run(debug=True, host='0.0.0.0', port=20000, threaded=True)

if __name__ == "__main__":
    main()
