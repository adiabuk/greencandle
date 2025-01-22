#!/usr/bin/env python
#pylint: disable=no-member
"""
Search for outliers in balances - run on production envs only
"""
import sys
from statistics import median
from send_nsca3 import send_nsca
from greencandle.lib.common import perc_diff, arg_decorator
from greencandle.lib.mysql import Mysql
from greencandle.lib import config
from greencandle.lib.logger import get_logger

@arg_decorator
def main():
    """
    Get all values from balance table and find outliers
    An outlier is a value that's more than 20% more than the average (median value)
    Send to nagios via NSCA
    """

    logger = get_logger(__name__)
    config.create_config()
    dbase = Mysql()
    raw_values = dbase.fetch_sql_data("select usd from balance where coin='TOTALS' "
                                      "and exchange_id = 5", header=False)
    values = [float(x[0]) for x in raw_values]
    med = median(values)
    results = []
    for value in values:
        try:
            results.append(round(abs(perc_diff(value, med)),2) > 20)
        except ZeroDivisionError:
            results.append(0)

    status = 2 if any(results) else 0
    msg = "CRITICAL: outliers found in balances" if any(results) else \
            "OK: no issues with balance table"

    send_nsca(status=status, host_name='jenkins',
              service_name=f'{config.main.base_env}-balance_outliers',
              text_output=msg, remote_host='nagios.amrox.loc')
    logger.info(msg)
    sys.exit(status)

if __name__ == '__main__':
    main()
