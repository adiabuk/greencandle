#pylint: disable=no-member,wrong-import-position

"""
Check current open trades for ability to close
"""

import sys
from binance import binance
from greencandle.lib import config
config.create_config()
from greencandle.lib.mysql import Mysql
from greencandle.lib.auth import binance_auth
from greencandle.lib.balance_common import get_step_precision
from greencandle.lib.alerts import send_slack_message

def main():
    """ Main function """

    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("Check current open trades for ability to close")
        sys.exit(0)

    account = config.accounts.binance[0]
    binance_auth(account)
    dbase = Mysql()
    query = ("select pair, base_in, name from trades where close_price is NULL")

    open_trades = dbase.fetch_sql_data(query, header=False)

    for trade in open_trades:
        pair, base_in, name = trade
        result = binance.spot_order(symbol=pair, side=binance.SELL,
                                    quantity=get_step_precision(pair, base_in),
                                    order_type=binance.MARKET, test=True)
        print("Testing {} from {}, result: {}".format(pair, name, str(result)))

        if result:
            send_slack_message("alerts", "Issue with open trade: {} {}".format(pair, name))

if __name__ == '__main__':
    main()
