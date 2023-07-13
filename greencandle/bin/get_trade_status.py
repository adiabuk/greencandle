#!/usr/bin/env python
#pylint: disable=no-member,too-many-locals
"""
Get details of current trades using mysql and current value from binance
"""

import sys
from greencandle.lib import config
from greencandle.lib.logger import exception_catcher
from greencandle.lib.mysql import Mysql
from greencandle.lib.redis_conn import Redis
from greencandle.lib.alerts import send_slack_message
from greencandle.lib.common import (get_tv_link, QUOTES, arg_decorator, divide_chunks,
                                    list_to_dict, get_be_services, get_trade_link)

config.create_config()
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
    redis = Redis(db=2)
    query_filter = sys.argv[1] if len(sys.argv) > 1 else ""
    name = f"{sys.argv[0].rsplit('/', maxsplit=1)[-1]}-{query_filter if query_filter else 'all'}"
    query = (f'select pair, name, open_time, concat(round(perc,2), " (", '
             f'round(net_perc,2), ")") as perc, open_price, '
             f'`interval`, direction from open_trades where name like "%{query_filter}%" order '
             f'by perc +0 ASC')
    services = list_to_dict(get_be_services(config.main.base_env), reverse=False, str_filter='-be-')
    open_trades = dbase.fetch_sql_data(query, header=False)
    header = ["pair", "name", "open_time", "perc", "open_price", "link", "tpsl"]
    chunks = list(divide_chunks(open_trades, 7))
    for chunk in chunks:
        chunk.insert(0, header)
        output = ""

        for trade in chunk:
            trade_direction = f"{trade[1]}-{trade[6]}" if \
                    not (trade[1].endswith('long') or trade[1].endswith('short')) else trade[1]
            try:
                short_name = services[trade_direction]

                trade[1] = short_name
                take = redis.conn.get(f"{trade[0]}:take_profit_perc:{short_name}")
                stop = redis.conn.get(f"{trade[0]}:stop_loss_perc:{short_name}")
                tpsl = f"{take.decode()}/{stop.decode()}"
                link = get_trade_link(trade[0], short_name, 'close', 'close_now',
                                      config.web.nginx_port)
            except (AttributeError, KeyError, IndexError):
                tpsl = "tpsl"
                link = "link"
            try:
                # remove interval from results
                direction = trade.pop(-1) if trade[0] != "pair" else ""
                interval = trade.pop(-1) if trade[0] != "pair" else ""
                output += "" if "name" in trade else \
                        (":short: " if "short" in direction else ":long: ")
                output += '   '.join([get_tv_link(item, interval) if str(item).endswith(QUOTES) \
                        else str(item) for item in trade[:-1]]) + " " + link + " " + tpsl + '\n'
            except IndexError:
                continue

        if len(chunk) > 1:
            send_slack_message('balance', output, name=name)
    if len(chunks) > 0:
        send_slack_message('balance', "*" * 20, name=name)
if __name__ == "__main__":
    main()
