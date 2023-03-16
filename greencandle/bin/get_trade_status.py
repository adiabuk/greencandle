#!/usr/bin/env python
#pylint: disable=wrong-import-position,no-member
"""
Get details of current trades using mysql and current value from binance
"""

import sys
from greencandle.lib import config
config.create_config()
from greencandle.lib.logger import exception_catcher
from greencandle.lib.mysql import Mysql
from greencandle.lib.alerts import send_slack_message
from greencandle.lib.common import (get_tv_link, QUOTES, arg_decorator, divide_chunks,
                                    list_to_dict, get_be_services, get_trade_link)

GET_EXCEPTIONS = exception_catcher((Exception))

@GET_EXCEPTIONS
@arg_decorator
def main():
    """
    Get list of open trades from DB, and format for output to slack with
    tradingview links for each trading pair -
    for periodic invocation from cron

    Usage: get_trade_status
    """

    dbase = Mysql()
    dbase.get_active_trades()
    query_filter = sys.argv[1] if len(sys.argv) > 1 else ""
    name = "{}-{}".format(sys.argv[0].split('/')[-1], query_filter if query_filter else "all")
    query = ('select pair, name, open_time, concat(round(perc,2), " (", '
             'round(net_perc,2), ")") as perc, open_price, direction, '
             '`interval` from open_trades where name like "%{}%" order '
             'by perc +0 ASC'.format(query_filter))
    services = list_to_dict(get_be_services(config.main.base_env), reverse=False)
    open_trades = dbase.fetch_sql_data(query, header=True)
    header = open_trades.pop(0)
    chunks = list(divide_chunks(open_trades, 7))
    for chunk in chunks:
        chunk.insert(0, header)
        output = ""

        for trade in chunk:
            try:
                trade_direction = "{}-{}".format(trade[1], trade[5]) if \
                        not (trade[1].endswith('long') or trade[1].endswith('short')) else trade[1]
                short_name = services[trade_direction]
                trade[1] = short_name
                link = get_trade_link(trade[0], short_name, 'close', 'close_now',
                                      config.web.nginx_port)
            except (KeyError, IndexError):
                link = "no-link"
            try:
                # remove interval from results
                interval = trade.pop(-1) if trade[0] != "pair" else ""
                output += "" if len(trade) > 5 and "name" in trade[1] else \
                        (":short: " if "short" in trade[-1] else ":long: ")
                output += '   '.join([get_tv_link(item, interval) if str(item).endswith(QUOTES) \
                        else str(item) for item in trade[:-1]]) + " " + link + '\n'
            except IndexError:
                continue

        if len(chunk) > 1:
            send_slack_message('balance', output, name=name)
    if len(chunks) > 0:
        send_slack_message('balance', "*" * 20, name=name)
if __name__ == "__main__":
    main()
