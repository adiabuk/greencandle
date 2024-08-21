#pylint: disable=no-member,too-many-locals,too-many-statements

"""
Check current open trades for ability to close
"""
import sys
from send_nsca3 import send_nsca
from str2bool import str2bool
from greencandle.lib.mysql import Mysql
from greencandle.lib import config
from greencandle.lib.balance_common import get_step_precision
from greencandle.lib.alerts import send_slack_message
from greencandle.lib.balance_common import get_base, get_quote
from greencandle.lib.common import arg_decorator, sub_perc
from greencandle.lib.balance import Balance
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
    query = "select pair, base_in, quote_in, name, direction from trades where close_price is NULL"

    open_trades = dbase.fetch_sql_data(query, header=False)
    bal = Balance(test=False)
    phemex = config.accounts.account2_type == 'phemex'
    balances = bal.get_balance(phemex=phemex)
    pairs = []
    prices = client.prices()
    count = 0
    for pair, base_in, quote_in, name, direction in open_trades:
        result = False
        result2 = False
        result3 = False
        result = client.spot_order(symbol=pair, side=client.sell,
                                   quantity=get_step_precision(pair, base_in),
                                   order_type=client.market, test=True)
        print(f"Testing {pair} from {name}, result: {str(result)}")
        print("comparing amount with available balance...")
        try:
            if 'isolated' in name:
                bal_amount = balances['isolated'][pair][get_base(pair)]

            elif 'cross' in name:

                if 'long' in direction:
                    bal_amount = balances['margin'][get_base(pair)]['gross_count']
                else:
                    bal_amount = balances['margin'][get_quote(pair)]['gross_count']

            else:
                bal_amount = balances['binance'][get_base(pair)]['count']
            if "long" in direction and sub_perc(dbase.get_complete_commission(),
                                           float(base_in)) > bal_amount:
                result2 = True
                reason = f"Not enough base amount for long: in:{base_in}, bal:{bal_amount}"

            elif "short" in direction and float(quote_in) > bal_amount:
                result2 = True
                reason = f"Not enough quote amount for short: in:{quote_in} bal:{bal_amount}"

            # Check if enough BNB
            quote = get_quote(pair)
            current_price = prices['BNB' + quote]
            bnb_required = (float(quote_in) / float(current_price))/100 * \
                    (dbase.get_complete_commission()/2)
            production = str2bool(config.main.production)
            account = 'binance' if not production or not 'cross' in name else 'margin'
            bnb_available = bal_amount = balances[account]['BNB']['gross_count']

            if float(bnb_required) > float(bnb_available):
                print(f"Insufficient BNB required:{bnb_required} available:{bnb_available}")
                result3 = "True"
                reason = "BNB not available"


        except KeyError as key_err:
            result2 = True
            reason = f"Unable to get balance: {str(key_err)}"
        if result or result2 or result3:
            count += 1
            pairs.append(f"{pair} ({name}): {reason}")

    str_pairs = '\n'.join(map(str, pairs))
    if str_pairs:
        status=1 if count == 1 else 2
        text_output = f"Issue with open_trades:\n{str_pairs}"
        send_slack_message("alerts", text_output,
                           name=sys.argv[0].rsplit('/', maxsplit=1)[-1])
    else:
        status=0
        text_output = "No issues with open trades"

    print(text_output)
    send_nsca(status=status, host_name='jenkins', service_name='open_trades',
              text_output=text_output.replace('\n',' '), remote_host='nagios.amrox.loc')

if __name__ == '__main__':
    main()
