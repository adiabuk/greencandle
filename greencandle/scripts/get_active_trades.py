#!/usr/bin/env python

"""
Get details of current trades using mysql and current value from binance
"""

from ..lib.mysql import Mysql
from ..lib import config

config.create_config()

def main():
    """ Main function """
    dbase = Mysql()
    dbase.get_active_trades()
    del dbase

if __name__ == "__main__":
    main()
