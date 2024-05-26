#pylint: disable=no-member,global-statement,no-name-in-module

"""
Fetch non-sensitive data from binance and provide via API endpoints
"""
import logging
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler
from setproctitle import setproctitle
from greencandle.lib import config
from greencandle.lib.logger import get_logger
from greencandle.lib.common import arg_decorator
from greencandle.lib.binance import Binance

config.create_config()
INTERVAL = config.main.interval
LOGGER = get_logger(__name__)
EXCHANGE_INFO = {}
APP = Flask(__name__)

def get_binance_info():
    """
    get exchange info from binance
    """
    global EXCHANGE_INFO
    client = Binance()
    EXCHANGE_INFO = client.exchange_info()

@APP.route('/exchange_info', methods=['GET'])
def get_exchange_info():
    """
    fetch exchange info from global var and return
    """
    return EXCHANGE_INFO


@arg_decorator
def main():
    """
    API for providing non-sensitive binance data fetched peridically
    """
    setproctitle(f"{config.main.base_env}-stream_binance")
    scheduler = BackgroundScheduler()
    scheduler.add_job(func=get_binance_info, trigger='interval', minutes=10)
    logging.basicConfig(level=logging.ERROR)
    scheduler.start()
    if float(config.main.logging_level) > 10:
        log = logging.getLogger('werkzeug')
        log.setLevel(logging.ERROR)
        log.disabled = True
    APP.run(debug=False, host='0.0.0.0', port=5000, threaded=True)

if __name__ == '__main__':
    main()
