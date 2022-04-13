#!/usr/bin/env python
#pylint: disable=wrong-import-position,wrong-import-order,no-member,logging-not-lazy,import-error,broad-except

"""
Analyze available data rom redis
Look for potential buys
"""

import sys
from apscheduler.schedulers.blocking import BlockingScheduler
from greencandle.lib import config
config.create_config()
from greencandle.lib.redis_conn import Redis
from greencandle.lib.logger import get_logger
from greencandle.lib.alerts import send_slack_message
from greencandle.lib.common import HOUR, MINUTE
from binance.binance import Binance

LOGGER = get_logger(__name__)
PAIRS = config.main.pairs.split()
MAIN_INDICATORS = config.main.indicators.split()
SCHED = BlockingScheduler()
INFO = Binance().exchange_info()

@SCHED.scheduled_job('cron', minute=MINUTE[config.main.interval],
                     hour=HOUR[config.main.interval], second="30")
def analyse_loop():
    """
    Gather data from redis and analyze
    """
    redis = Redis(interval=config.main.interval, test=False)
    for pair in PAIRS:
        LOGGER.debug("Analysing pair: %s" % pair)
        try:
            result = redis.get_action(pair=pair, interval=config.main.interval)[0]

            if result == "OPEN":
                LOGGER.debug("Items to buy")
                margin = "margin" if INFO[pair]['isMarginTradingAllowed'] else "spot"
                pair_link = ("<https://www.tradingview.com/chart/?symbol=BINANCE:{0}|{0}>"
                             .format(pair))
                send_slack_message("notifications", "Open: %s %s %s %s" %
                                   (pair_link, config.main.interval,
                                    config.main.trade_direction, margin), emoji=True)
        except Exception as err_msg:
            LOGGER.critical("Error with pair %s %s" % (pair, str(err_msg)))
    LOGGER.info("End of current loop")
    del redis

def main():
    """
    Main function
    """

    usage = "Usage: {}".format(sys.argv[0])
    if len(sys.argv) > 1 and  sys.argv[1] == '--help':
        print(usage)
        sys.exit(0)
    LOGGER.info("Starting Initial loop")
    analyse_loop()
    LOGGER.info("Finished Initial loop")
    SCHED.start()

if __name__ == "__main__":
    main()
