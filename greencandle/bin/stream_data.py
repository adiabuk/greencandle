#pylint: disable=no-member,unused-argument,no-name-in-module

"""
Stream candle data from binance and make latest data available through flask

For use in data environment, uses pairs and interval within scope
"""
import json
import logging
import threading
import websocket
from flask import Flask, request, Response
from setproctitle import setproctitle
from greencandle.lib import config
from greencandle.lib.logger import get_logger
from greencandle.lib.common import arg_decorator
from greencandle.lib.alerts import send_slack_message

config.create_config()
INTERVAL = config.main.interval
APP = Flask(__name__)
LOGGER = get_logger(__name__)
RECENT = {}
CLOSED = {}
PAIR_STRING = ""

for pair in config.main.pairs.split():
    PAIR_STRING += f"/{pair.lower()}@kline_{INTERVAL}"

def on_open(socket):
    """
    print when socket is opened
    """
    send_slack_message("alerts", "ws socket opened")
    LOGGER.info("ws socket opened")

def on_message(socket, message):
    """
    When data received through socket
    """
    json_message = json.loads(message)
    candle = json_message['data']['k']
    current_dict = {'openTime': candle['t'], 'closeTime': candle['T'], 'open': candle['o'],
                    'high': candle['h'], 'low': candle['l'], 'close': candle['c'],
                    'quoteVolume': candle['q'], 'volume': candle['v'], 'numTrades': candle['n']}
    RECENT[candle['s']] = current_dict

    if candle['x']:  # closed candle (bool)
        CLOSED[candle['s']] = current_dict

def on_close(socket, close_status_code, close_msg):
    """
    Print when socket is closed
    """
    send_slack_message("alerts", "ws socket closed")
    LOGGER.info("ws socket closed")

@APP.route('/recent', methods=['GET'])
def serve_recent():
    """
    closed candle data request through flask API
    """
    try:
        return RECENT[request.args.get('pair')]
    except KeyError:
        return Response(None, status=400,)

@APP.route('/closed', methods=['GET'])
def serve_closed():
    """
    recent data request through flask API
    """
    try:
        return CLOSED[request.args.get('pair')]
    except KeyError:
        return Response(None, status=400,)

@APP.route('/all', methods=['GET'])
def serve_all():
    """
    return recent and closed data for all pairs as dict
    """
    return {'recent': RECENT, 'closed': CLOSED}

def on_error(socket, error):
    """
    Raise errors from websocket
    """
    LOGGER.critical(str(error))

def start_ws():
    """
    Start websocket app
    """
    sock = "wss://stream.binance.com:443/stream?streams=" + PAIR_STRING.lstrip('/')

    socket = websocket.WebSocketApp(sock, on_open=on_open, on_close=on_close,
                                    on_message=on_message, on_error=on_error)
    socket.run_forever(reconnect=5)

def start_flask():
    """
    Start flask app
    """
    if float(config.main.logging_level) > 10:
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        log.disabled = True
    APP.run(debug=False, host='0.0.0.0', port=5000, threaded=True)

@arg_decorator
def main():
    """
    Stream candle data from binance and make latest data available through flask

    For use in data environment, uses pairs and interval within scope
    """
    setproctitle(f"{config.env.base_env}-stream_data-{INTERVAL}")
    t_flask = threading.Thread(target=start_flask)
    t_ws = threading.Thread(target=start_ws)

    t_flask.start()
    t_ws.start()

    t_flask.join()
    t_ws.join()

if __name__ == '__main__':
    main()
