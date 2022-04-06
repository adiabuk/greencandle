#!/usr/bin/env python
#pylint: disable=wrong-import-position,no-member,logging-not-lazy,import-error,bare-except

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


def test_loop(interval):
    redis = Redis(interval=interval, test=False)
    #engine = Engine(prices=prices_trunk, dataframes=dataframes, interval=interval, redis=redis)
    #engine.get_data(localconfig=MAIN_INDICATORS, first_run=False)
    #dataframes = get_dataframes(PAIRS, interval=interval, no_of_klines=1)
    for pair in PAIRS:
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

    #del engine
    del redis


def prod_run():
    """
    Prod run
    """
    interval = config.main.interval
    LOGGER.info("Starting prod run")
    test_loop(interval)
    LOGGER.info("Finished prod run")

def main():
    """
    Main function
    """
