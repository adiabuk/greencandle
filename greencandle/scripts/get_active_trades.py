#!/usr/bin/env python
#pylint: disable=wrong-import-position

"""
Get details of current trades using mysql and current value from binance
"""

from ..lib import config
config.create_config()

from ..lib.mysql import Mysql

def main():
    """ Main function """
    dbase = Mysql()
    dbase.get_active_trades()
    del dbase

if __name__ == "__main__":
    main()
