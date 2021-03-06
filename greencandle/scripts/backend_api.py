#!/usr/bin/env python
#pylint: disable=wrong-import-position,no-member,logging-not-lazy

"""
API trading module
"""
import sys
from time import strftime, gmtime
from flask import Flask, request, Response
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
    print("hi")
    print("pair,action:", request.json)
    pair = request.json['pair']
    action = request.json['action']
    text = request.json['text']
    LOGGER.info("Request received: %s %s %s" %(pair, action, text))
    current_time = strftime("%Y-%m-%d %H:%M:%S", gmtime())
    current_price = get_current_price(pair)
    item = [(pair, current_time, current_price, config.main.name)]
    trade = Trade(interval=config.main.interval, test_data=False, test_trade=TEST)
    if action == 'buy':
        trade.open_trade(item)
    elif action == 'sell':
        trade.close_trade(item, drawdowns={pair:0}, drawups={pair:0})
    return Response(status=200)

def main():
    """
    main function
    """
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("API for executing trades")
        sys.exit(0)


    APP.run(debug=True, host='0.0.0.0', port=20000, threaded=True)
if __name__ == "__main__":
    main()
