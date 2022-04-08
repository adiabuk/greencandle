#pylint: disable=no-member,wrong-import-position

"""
Check current open trades for ability to close
"""

import sys
from greencandle.lib.mysql import Mysql
from greencandle.lib.balance_common import get_step_precision
from greencandle.lib.alerts import send_slack_message
from greencandle.lib.balance_common import get_base
from greencandle.lib.balance import Balance
from greencandle.lib.auth import binance_auth

def main():
    """ Main function """
    client = binance_auth()
    if len(sys.argv) > 1 and sys.argv[1] == '--help':
        print("Check current open trades for ability to close")
        sys.exit(0)

    dbase = Mysql()
    query = ("select pair, base_in, name from trades where close_price is NULL")

    open_trades = dbase.fetch_sql_data(query, header=False)
    bal = Balance(test=False)
    balances = bal.get_balance()
    pairs = []
    for trade in open_trades:
        pair, base_in, name = trade
        result = client.spot_order(symbol=pair, side=client.SELL,
                                   quantity=get_step_precision(pair, base_in),
                                   order_type=client.MARKET, test=True)
        print("Testing {} from {}, result: {}".format(pair, name, str(result)))
        print("comparing amount with available balance...")
        try:
            if 'isolated' in name:
                bal_amount = balances['isolated'][pair][get_base(pair)]
            elif 'cross' in name:
                bal_amount = balances['margin'][get_base(pair)]['count']
            else:
                bal_amount = balances['binance'][get_base(pair)]['count']
            result2 = float(base_in) > bal_amount
        except KeyError:
            result2 = True

        if result or result2:
            pairs.append("{} ({})".format(pair, name))

    str_pairs = '\n'.join(map(str, pairs))
    if str_pairs:
        send_slack_message("alerts", "Issues with open trades:\n {}".format(str_pairs))

if __name__ == '__main__':
    main()
