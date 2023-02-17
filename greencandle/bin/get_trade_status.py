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
from greencandle.lib.common import get_tv_link, QUOTES, arg_decorator, divide_chunks

@arg_decorator
def main():
    """
    Get list of open trades from DB, and format for output to slack with
    tradingview links for each trading pair -
    for periodic invocation from cron

    Usage: get_trade_status
    """

    dbase = Mysql()

    query = ('select pair, name, open_time, concat(round(perc,2), " (", '
             'round(net_perc,2), ")") as perc, usd_quantity, direction, '
             '`interval` from open_trades order by perc +0 DESC')

    open_trades = dbase.fetch_sql_data(query, header=True)
    header = open_trades.pop(0)
    chunks = list(divide_chunks(open_trades, 10))
    for chunk in chunks:
        chunk.insert(0, header)
        output = ""

        for trade in chunk:
            interval = trade.pop(-1)  # remove interval from results
            output += "" if "name" in trade[1] else \
                    (":short: " if "short" in trade[-1] else ":long: ")
            output += '   '.join([get_tv_link(item, interval) if str(item).endswith(QUOTES) else \
                str(item).replace("-api-any", "") for item in trade[:-1]]) + '\n'

        if len(chunk) > 1:
            send_slack_message('balance', output, name=sys.argv[0].split('/')[-1])
    send_slack_message('balance', "*" * 20, name=sys.argv[0].split('/')[-1])
if __name__ == "__main__":
    main()
