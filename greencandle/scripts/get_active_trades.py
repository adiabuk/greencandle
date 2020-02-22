#!/usr/bin/env python
#pylint: disable=wrong-import-position

"""
Get details of current trades using mysql and current value from binance
"""

import sys
from ..lib import config
config.create_config()

from ..lib.mysql import Mysql

def main():
    """ Main function """
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("Get list of current trades from mysql")
    sys.exit(0)
    dbase = Mysql()
    dbase.get_active_trades()
    del dbase

if __name__ == "__main__":
    main()
