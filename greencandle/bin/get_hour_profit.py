#!/usr/bin/env python
#pylint: disable=too-many-locals,no-member,expression-not-assigned
"""
Get profit from prvious hour and send to slack
"""

import sys
from datetime import datetime
from greencandle.lib.alerts import send_slack_message
from greencandle.lib.logger import exception_catcher
from greencandle.lib.common import format_usd, arg_decorator
from greencandle.lib import config
from greencandle.lib.mysql import Mysql
from greencandle.lib.web import push_prom_data

GET_EXCEPTIONS = exception_catcher((Exception))

@GET_EXCEPTIONS
@arg_decorator
def main():
    """
    Get Average, total and USD profit for last hour of trading
    Usage: get_hour_balance
    """
    config.create_config()
    env = config.main.base_env
    mysql = Mysql()

    total_perc, total_net_perc, avg_perc, avg_net_perc, usd_profit, usd_net_profit, num_hour, \
            hour = mysql.get_last_hour_profit()

    todays_usd, todays_net_usd, todays_avg, todays_net_avg, todays_total, todays_net_total, \
    num_day = mysql.get_todays_profit()

    if total_perc and todays_total:
        message = (f"Profit for Hour {hour}\n"
                   f"Total perc: {total_perc:.2f}% ({total_net_perc:.2f}%) ~{num_hour} trades\n"
                   f"Average perc: {avg_perc:.2f}% ({avg_net_perc:.2f}%)\n"
                   f"USD profit: {format_usd(usd_profit)} ({format_usd(usd_net_profit)})\n"
                   f"Today's avg profit: {todays_avg:.2f}% ({todays_net_avg:.2f}%)\n"
                   f"Today's USD profit: {format_usd(todays_usd)} ({format_usd(todays_net_usd)})\n"
                   f"Today's total profit: {todays_total:.2f}% ({todays_net_total:.2f}%) "
                   f"~{num_day} trades\n")

        now = datetime.now()
        if 0 < now.minute < 10:
            send_slack_message('balance', message, name=sys.argv[0].rsplit('/', maxsplit=1)[-1])

    prom_data = {f'closed_profit_perc_hour_{env}': total_net_perc,
                 f'closed_profit_perc_day_{env}': todays_net_total,
                 f'closed_net_avg_hour_{env}': avg_perc,
                 f'closed_net_avg_day_{env}': todays_avg,
                 f'closed_net_profit_hour_{env}': usd_profit,
                 f'closed_net_profit_day_{env}': todays_usd}
    for promkey, promval in prom_data.items():
        push_prom_data(promkey, promval)


if __name__ == "__main__":
    main()
