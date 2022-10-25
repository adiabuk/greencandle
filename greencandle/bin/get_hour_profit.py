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

    total_perc, total_net_perc, avg_perc, avg_net_perc, usd_profit, usd_net_profit, num_hour, \
            hour = mysql.get_last_hour_profit()

    todays_avg, todays_net_avg, todays_total, todays_net_total, num_day = mysql.get_todays_profit()

    if avg_perc:
        message = ("Profit for Hour {0}\n"
                   "Total perc: {1:.2f}% ({2:.2f}%) ~{3} trades\n"
                   "Average perc: {4:.2f}% ({5:.2f}%)\n"
                   "USD profit: {6} ({7})\n"
                   "Today's avg profit: {8:.2f}% ({9:.2f}%)\n"
                   "Today's total profit: {10:.2f}% ({11:.2f}%) ~{12} trades\n"
                   .format(hour, total_perc, total_net_perc, num_hour, avg_perc, avg_net_perc,
                           format_usd(usd_profit), format_usd(usd_net_profit),
                           todays_avg, todays_net_avg, todays_total, todays_net_total, num_day))

        send_slack_message('balance', message, name=sys.argv[0].split('/')[-1])

if __name__ == "__main__":
    main()
