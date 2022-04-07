#!/usr/bin/env python
#pylint: disable=wrong-import-position,no-member,logging-not-lazy,import-error,bare-except

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
LOGGER = get_logger(__name__)
PAIRS = config.main.pairs.split()
MAIN_INDICATORS = config.main.indicators.split()
SCHED = BlockingScheduler()

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
            result, _, _, _, _ = redis.get_action(pair=pair, interval=interval)
            current_candle = dataframes[pair].iloc[-1]
            redis.update_drawdown(pair, current_candle)
            redis.update_drawup(pair, current_candle)

            if result == "OPEN":
                LOGGER.debug("Items to buy")
                margin = "margin" if info[pair]['isMarginTradingAllowed'] else "spot"
                send_slack_message("notifications", "Buy: %s %s 4h" % (pair, margin))
        except:
            LOGGER.critical("Error with pair %s" % pair)
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
    SCHED.start()

if __name__ == "__main__":
    main()
