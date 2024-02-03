"""
Borrow amount from exchange
"""

import sys
from greencandle.lib.auth import binance_auth
from greencandle.lib import config
from greencandle.lib.mysql import Mysql
from greencandle.lib.binance_accounts import quote2base
from greencandle.lib.binance import BinanceException
from greencandle.lib.common import Bcolours, arg_decorator

@arg_decorator
def main():
    """
    Borrow amount from exchange
    Amount is fixed from db 'max_trade_usd' value
    will be converted into equivalent of asset amount required
    Usage: borrow_amount <asset> (eg. BTC)
    """
    config.create_config()
    client = binance_auth()
    dbase = Mysql()
    usd_amount = dbase.get_var_value('max_trade_usd')
    print(f'usd amount to borrow: {usd_amount}')
    symbol = sys.argv[1]
    amount = quote2base(usd_amount, symbol + 'USDT')
    print(f'base amount to borrow: {amount}')

    try:
        borrow_res = client.margin_borrow(symbol=None, quantity=amount, isolated=False,
                                          asset=symbol)
        print(borrow_res)
        print(f'{Bcolours.OKGREEN}DONE{Bcolours.ENDC}')
    except BinanceException as ex:
        print(ex)
        print(f'{Bcolours.FAIL}FAILED{Bcolours.ENDC}')


if __name__ == '__main__':
    main()
