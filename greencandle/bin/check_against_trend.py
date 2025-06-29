#!/usr/bin/env python
# pylint: disable=no-member
"""
Count number of open trades running against trend
using drain for interval/env and send to nagios
"""

import sys
from send_nsca3 import send_nsca
from greencandle.lib.mysql import Mysql
from greencandle.lib import config
from greencandle.lib.logger import get_logger
from greencandle.lib.common import arg_decorator
from greencandle.lib.sentiment import Sentiment

@arg_decorator
def main():
    """
    Check number of open trades and compare against drain for given scope
    """
    logger = get_logger(__name__)
    config.create_config()
    env = config.main.base_env
    dbase = Mysql()
    long_count = 0
    short_count = 0

    sentiment = Sentiment()
    result = int(sentiment.get_hl_dir('30m'))
    for interval in ('15m', '1h', '30m', '4h'):

        if result > 0:
            count = len(dbase.get_open_trades(name_filter=interval, direction_filter='short'))
            short_count += count
        if result < 0:
            count = len(dbase.get_open_trades(name_filter=interval, direction_filter='long'))
            long_count += count

    total = long_count + short_count
    if total > 10:
        msg = 'CRITICAL'
        status = 2
    elif total > 0:
        msg = 'WARNING'
        status = 1
    else:
        msg = 'OK'
        status = 0


    send_nsca(status=status, host_name='eaglenest', service_name=f'{env}_against_trend',
              text_output=f'{msg} {total} number of trades against trend; long: '
                          f'{long_count}, short: {short_count};total={total};;;;',
              remote_host='nagios.amrox.loc')

    logger.info('%s  trades exist against short trend', long_count)
    logger.info('%s trades exist against long trend', short_count)
    sys.exit(status)

if __name__ == "__main__":
    main()
