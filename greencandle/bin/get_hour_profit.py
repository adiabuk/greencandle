#!/usr/bin/env python
#pylint: disable=too-many-locals
"""
Get profit from prvious hour and send to slack
"""

import sys
from greencandle.lib.alerts import send_slack_message
from greencandle.lib.logger import exception_catcher
from greencandle.lib.common import format_usd, arg_decorator
from greencandle.lib.mysql import Mysql

GET_EXCEPTIONS = exception_catcher((Exception))

@GET_EXCEPTIONS
@arg_decorator
def main():
    """
    Get Average, total and USD profit for last hour of trading
    Usage: get_hour_balance
    """
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

        send_slack_message('balance', message, name=sys.argv[0].rsplit('/', maxsplit=1)[-1])

if __name__ == "__main__":
    main()
