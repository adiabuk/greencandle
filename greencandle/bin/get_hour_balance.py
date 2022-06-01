#!/usr/bin/env python
"""
Get profit from prvious hour and send to slack
"""

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
    total_perc, avg_perc, usd_profit, hour = mysql.get_last_hour_profit()
    todays_perc = mysql.get_todays_profit()
    message = ("Profit for Hour {0}\n"
               "Total perc: {1:.2f}%\n"
               "Average perc: {2:.2f}%\n"
               "USD profit: {3}\n"
               "Today's profit: {4:.2f}%".format(hour, total_perc, avg_perc,
                                                 format_usd(usd_profit), todays_perc))
    send_slack_message('balance', message)

if __name__ == "__main__":
    main()
