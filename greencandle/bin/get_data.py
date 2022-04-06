#!/usr/bin/env python
#pylint: disable=wrong-import-position,no-member,logging-not-lazy,import-error,bare-except

import sys
from binance import binance
from apscheduler.schedulers.blocking import BlockingScheduler
from greencandle.lib import config
config.create_config()
from greencandle.lib.redis_conn import Redis
from greencandle.lib.engine import Engine
from greencandle.lib.run import prod_initial
from greencandle.lib.binance_common import get_dataframes
from greencandle.lib.logger import get_logger
from greencandle.lib.alerts import send_slack_message
from greencandle.lib.common import HOUR, MINUTE

LOGGER = get_logger(__name__)
PAIRS = config.main.pairs.split()
MAIN_INDICATORS = config.main.indicators.split()
SCHED = BlockingScheduler()

def test_loop(interval=None):
    """
    Test loop
    """
    LOGGER.debug("Performaing prod loop")
    LOGGER.info("Pairs in config: %s" % PAIRS)
    LOGGER.info("Total unique pairs: %s" % len(PAIRS))

    LOGGER.info("Starting new cycle")
    LOGGER.debug("max trades: %s" % config.main.max_trades)

    prices = binance.prices()
    info = binance.exchange_info()
    prices_trunk = {}

    for key, val in prices.items():
        if key in PAIRS:
            prices_trunk[key] = val
    LOGGER.info("Getting dataframes for all pairs")
    dataframes = get_dataframes(PAIRS, interval=interval, max_workers=1)
    LOGGER.info("Done getting dataframes")

    redis = Redis(interval=interval, test=False)
    engine = Engine(prices=prices_trunk, dataframes=dataframes, interval=interval, redis=redis)
    engine.get_data(localconfig=MAIN_INDICATORS, first_run=False)
    dataframes = get_dataframes(PAIRS, interval=interval, no_of_klines=1)
    #for pair in PAIRS:
    #    try:
    #        result, _, _, _, _ = redis.get_action(pair=pair, interval=interval)
    #        current_candle = dataframes[pair].iloc[-1]
    #        redis.update_drawdown(pair, current_candle)
    #        redis.update_drawup(pair, current_candle)

    #        if result == "OPEN":
    #            LOGGER.debug("Items to buy")
    #            margin = "margin" if info[pair]['isMarginTradingAllowed'] else "spot"
    #            send_slack_message("notifications", "Buy: %s %s 4h" % (pair, margin))
    #    except:
    #        LOGGER.critical("Error with pair %s" % pair)

    #del engine
    #del redis

@SCHED.scheduled_job('cron', minute=MINUTE[config.main.interval],
                     hour=HOUR[config.main.interval], second="30")
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
    interval = config.main.interval
    LOGGER.info("Starting initial prod run")
    redis = Redis(interval=interval, test=False)
    redis.clear_all()
    del redis
    prod_initial(interval) # initial run, before scheduling begins
    LOGGER.info("Finished initial prod run")
    prod_run()

    try:
        SCHED.start()
    except KeyboardInterrupt:
        LOGGER.warning("\nExiting on user command...")
        sys.exit(1)


if __name__ == '__main__':
    main()
