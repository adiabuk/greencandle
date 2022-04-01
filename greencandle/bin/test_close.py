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
from greencandle.lib.balance_common import get_base
from greencandle.lib.balance import Balance

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
    bal = Balance(test=False)
    balances = bal.get_balance()
    for trade in open_trades:
        pair, base_in, name = trade
        result = binance.spot_order(symbol=pair, side=binance.SELL,
                                    quantity=get_step_precision(pair, base_in),
                                    order_type=binance.MARKET, test=True)
        print("Testing {} from {}, result: {}".format(pair, name, str(result)))
        print("comparing amount with available balance...")
        try:
            if 'isolated' in name:
                bal_amount = balances['isolated'][pair][get_base(pair)]
            elif 'cross' in name:
                bal_amount = balances['margin'][get_base(pair)]['count']
            else:
                bal_amount = balances['binance'][get_base(pair)]['count']
            result2 = float(base_in) < bal_amount
        except KeyError:
            result2 = True

        if result or result2:
            send_slack_message("alerts", "Issue with open trade: {} {}".format(pair, name))

if __name__ == '__main__':
    main()
