#pylint: disable=no-member,wrong-import-position

"""
Check current open trades for ability to close
"""
import sys
from str2bool import str2bool
from greencandle.lib.mysql import Mysql
from greencandle.lib import config
from greencandle.lib.balance_common import get_step_precision
from greencandle.lib.alerts import send_slack_message
from greencandle.lib.balance_common import get_base, get_quote
from greencandle.lib.common import arg_decorator
from greencandle.lib.balance import Balance
from greencandle.lib.binance_accounts import quote2base
from greencandle.lib.auth import binance_auth
config.create_config()

@arg_decorator
def main():
    """
    Check that we have enough base currency to close the trade
    and enough BNB to pay for commission costs
    Alert in slack and to logs

    Usage: test_close
    """
    client = binance_auth()

    dbase = Mysql()
    query = ("select pair, base_in, quote_in, name from trades where close_price is NULL")

    open_trades = dbase.fetch_sql_data(query, header=False)
    bal = Balance(test=False)
    phemex = config.accounts.account2_type == 'phemex'
    balances = bal.get_balance(phemex=phemex)
    pairs = []
    prices = client.prices()
    for trade in open_trades:
        result = False
        result2 = False
        result3 = False
        pair, base_in, quote_in, name = trade
        result = client.spot_order(symbol=pair, side=client.sell,
                                   quantity=get_step_precision(pair, base_in),
                                   order_type=client.market, test=True)
        print("Testing {} from {}, result: {}".format(pair, name, str(result)))
        print("comparing amount with available balance...")
        try:
            if 'isolated' in name:
                bal_amount = balances['isolated'][pair][get_base(pair)]
            elif 'cross' in name:
                if 'long' in name:
                    bal_amount = balances['margin'][get_base(pair)]['count']
                else:
                    bal_amount = quote2base(quote_in, pair)

            else:
                bal_amount = balances['binance'][get_base(pair)]['count']
            if float(base_in) > bal_amount:
                result2 = True
                reason = "Not enough base amount"

            # Check if enough BNB
            quote = get_quote(pair)
            current_price = prices['BNB' + quote]
            bnb_required = (float(quote_in) / float(current_price))/100 *0.1
            production = str2bool(config.main.production)
            account = 'binance' if not production or not 'cross' in name else 'margin'
            bnb_available = bal_amount = balances[account]['BNB']['count']

            if float(bnb_required) > float(bnb_available):
                print("Insufficient BNBrequired:{} available:{}".format(bnb_required,
                                                                        bnb_available))
                result3 = "True"
                reason = "BNB not available"


        except KeyError as key_err:
            result2 = True
            reason = "Unable to get balance: {}".format(str(key_err))
        if result or result2 or result3:
            pairs.append("{} ({}): {}".format(pair, name, reason))

    str_pairs = '\n'.join(map(str, pairs))
    if str_pairs:
        send_slack_message("alerts", "Issues with open trades:\n {}".format(str_pairs),
                           name=sys.argv[0].split('/')[-1])

if __name__ == '__main__':
    main()
