#!/usr/bin/env python
#pylint: disable=wrong-import-position

"""
Get details of current trades using mysql and current value from binance
"""

from greencandle.lib.common import arg_decorator
from greencandle.lib.mysql import Mysql

@arg_decorator
def main():
    """
    Get list of active trades and store in db active_trades table with updated current price
    Also store amount in USD, and perc

    To be used with cron, to periodically update db

    Usage: get_active_trades
    """

    dbase = Mysql()
    dbase.get_active_trades()
    del dbase

if __name__ == "__main__":
    main()
