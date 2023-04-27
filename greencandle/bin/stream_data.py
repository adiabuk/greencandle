#pylint: disable=no-member, global-statement, unused-argument

"""
Stream candle data from binance and make latest data available through flask

For use in data environment, uses pairs and interval within scope
"""
import json
import threading
import websocket
from flask import Flask, request

from greencandle.lib.common import arg_decorator
from greencandle.lib import config
config.create_config()
APP = Flask(__name__)
DATA = {}
PAIR_STRING = ""
for pair in config.main.pairs.split():
    PAIR_STRING += "/{}@kline_{}".format(pair.lower(), config.main.interval)

def on_open(socket):
    """
    print when socket is opened
    """
    print("open")

def on_message(socket, message):
    """
    When data received through socket
    """
    global DATA
    json_message = json.loads(message)
    candle = json_message['data']['k']
    raw = json.dumps(candle, indent=2)
    raw = candle
    current_dict = {'openTime': raw['t'], 'closeTime': raw['T'], 'open': raw['o'], 'high': raw['h'],
                    'low': raw['l'], 'close': raw['c'], 'quoteVolume': raw['q'], 'volume': raw['v'],
                    'numTrades': raw['n']}
    DATA[raw['s']] = current_dict
    #is_candle_closed = candle['x']

def on_close(socket, close_status_code, close_msg):
    """
    Print when socket is closed
    """
    print("closed")

@APP.route('/recent', methods=['GET'])
def serve_recent():
    """
    data request through flask API
    """
    return DATA[request.args.get('pair')]


def start_ws():
    """
    Start websocket app
    """
    sock = "wss://stream.binance.com:9443/stream?streams=" + PAIR_STRING.lstrip('/')

    socket = websocket.WebSocketApp(sock, on_open=on_open, on_close=on_close,
                                    on_message=on_message)
    socket.run_forever()

def start_flask():
    """
    Start flask app
    """
    APP.run(debug=False, host='0.0.0.0', port=5000, threaded=True)

@arg_decorator
def main():
    """
    Stream candle data from binance and make latest data available through flask

    For use in data environment, uses pairs and interval within scope
    """

    p_flask = threading.Thread(target=start_flask)
    p_ws = threading.Thread(target=start_ws)

    p_flask.start()
    p_ws.start()

    p_flask.join()
    p_ws.join()

if __name__ == '__main__':
    main()
