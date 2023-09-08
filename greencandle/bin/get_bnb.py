#!/usr/bin/env python

"""
Slack alert when not enough available BNB
"""

import sys
from greencandle.lib.common import arg_decorator
from greencandle.lib.balance import Balance
from greencandle.lib.alerts import send_slack_message

@arg_decorator
def main():
    """
    Slack alert when not enough available BNB
    Usage: get_bnb
    """

    balance = Balance(test=False)
    all_bal = balance.get_balance()
    bnb = float(all_bal['margin']['BNB']['gross_count'])
    if bnb < 0.1:
        error_str = "Not enough BNB in cross margin account"
        send_slack_message('alerts', error_str, name=sys.argv[0].rsplit('/', maxsplit=1)[-1])


if __name__ == "__main__":
    main()
