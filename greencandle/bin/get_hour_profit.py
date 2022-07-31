#!/usr/bin/env python
#pylint: disable=unbalanced-tuple-unpacking

"""
Get profit from prvious hour and send to slack
"""

import sys
from greencandle.lib.alerts import send_slack_message
from greencandle.lib.common import format_usd, arg_decorator
from greencandle.lib.mysql import Mysql

@arg_decorator
def main():
    """
    Get Average, total and USD profit for last hour of trading
    Usage: get_hour_balance
    """
    mysql = Mysql()

    total_perc, total_net_perc, avg_perc, avg_net_perc, usd_profit, usd_net_profit, hour \
            = mysql.get_last_hour_profit()

    todays_avg, todays_net_avg, todays_total, todays_net_total = mysql.get_todays_profit()

    if todays_total:
        message = ("Profit for Hour {0}\n"
                   "Total perc: {1:.2f}%({2:.2f}%)\n"
                   "Average perc: {3:.2f}%({4:.2f}%)\n"
                   "USD profit: {5}({6})\n"
                   "Today's avg profit: {7:.2f}%({8:.2f}%)\n"
                   "Today's total profit: {9:.2f}%({10:.2f}%)\n"
                   .format(hour, total_perc, total_net_perc, avg_perc, avg_net_perc,
                           format_usd(usd_profit), format_usd(usd_net_profit),
                           todays_avg, todays_net_avg, todays_total, todays_net_total))

        send_slack_message('balance', message, name=sys.argv[0].split('/')[-1])

if __name__ == "__main__":
    main()
