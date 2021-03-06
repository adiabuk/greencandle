#!/usr/bin/env python
#pylint: disable=wrong-import-position,no-member
"""
Get details of current trades using mysql and current value from binance
"""

import sys
from ..lib import config
config.create_config()
from ..lib.mysql import Mysql
from ..lib.alerts import send_slack_message

def main():
    """ Main function """

    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("Get open trades status")
        sys.exit(0)

    dbase = Mysql()

    query = ("select pair, name, open_time, round(perc,2) as perc from "
             "open_trades order by perc DESC")
    open_trades = dbase.fetch_sql_data(query, header=False)
    output = ""
    for trade in open_trades:
        output += '\t\t'.join([str(item) for item in trade]) + '\n'
    if output:
        send_slack_message('balance', output)
    sys.exit()

if __name__ == "__main__":
    main()
