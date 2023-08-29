#!/usr/bin/env python
"""
Find pairs with small loans and no open trades to convert to USDT
"""

from greencandle.lib.auth import binance_auth
from greencandle.lib.mysql import Mysql
from greencandle.lib.balance_common import get_base, get_quote
from greencandle.lib.common import arg_decorator


@arg_decorator
def main():
    """
    Find pairs with small loans and no open trades to convert to USDT
    """
    client = binance_auth()
    cross_details = client.get_cross_margin_details()
    borrowed_set = set()

    for item in cross_details['userAssets']:
        if float(item['borrowed']) > 0:
            borrowed_set.add(item['asset'])
            #borrowed_set.add((item['asset'], item['borrowed']))

    dbase = Mysql()
    open_trades = dbase.fetch_sql_data('select pair, direction from open_trades',
                                       header=False)
    open_set = set()
    for pair, direction in open_trades:
        if direction == 'short':
            open_set.add(get_base(pair))
        else:
            open_set.add(get_quote(pair))
    main_set = set(borrowed_set - open_set)
    redeemable = client.get_small_liability_set()
    final = list(main_set.intersection(redeemable))

    li_of_lis = []
    start = 0
    end = len(final)
    step = 10
    for item in range(start, end, step):
        li_of_lis.append(final[item:item+step])

    for current_li in li_of_lis[:3]:
        client.small_liability_exchange(current_li)
if __name__ == '__main__':
    main()
