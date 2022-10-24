#!/usr/bin/env python
#pylint: disable=wrong-import-position,no-member
"""
Get details of current trades using mysql and current value from binance
"""

import sys
from greencandle.lib import config
config.create_config()
from greencandle.lib.mysql import Mysql
from greencandle.lib.alerts import send_slack_message
from greencandle.lib.common import get_tv_link, QUOTES, arg_decorator

@arg_decorator
def main():
    """
    Get list of open trades from DB, and format for output to slack with
    tradingview links for each trading pair -
    for periodic invocation from cron

    Usage: get_trade_status
    """

    dbase = Mysql()

    query = ('select pair, name, direction open_time, concat(round(perc,2), " (", '
             'round(net_perc,2), ")") as perc, usd_quantity, direction from open_trades '
             'order by perc +0 DESC')

    open_trades = dbase.fetch_sql_data(query, header=True)
    output = ""

    for trade in open_trades:
        output += "" if "name" in trade[1]  else (":short: " if "short" in trade[2] else ":long: ")
        output += '   '.join([get_tv_link(item) if str(item).endswith(QUOTES) else \
                str(item).replace("-api-any", "") for item in trade[:-1]]) + '\n'

    if len(open_trades) > 1:
        send_slack_message('balance', output, name=sys.argv[0].split('/')[-1])
if __name__ == "__main__":
    main()
