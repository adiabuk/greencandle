#pylint:disable=too-many-locals
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

    # get unique set of assets which have a loan against tem
    for item in cross_details['userAssets']:
        if float(item['borrowed']) > 0:
            borrowed_set.add(item['asset'])

    dbase = Mysql()
    open_trades = dbase.fetch_sql_data('select pair, direction from open_trades',
                                       header=False)
    # get unique set of pairs with open trades
    # get assets from pairs, base if short, quote if long
    open_set = set()
    for pair, direction in open_trades:
        if direction == 'short':
            open_set.add(get_base(pair))
        else:
            open_set.add(get_quote(pair))

    # get assets with loan which are not in a trade
    main_set = set(borrowed_set - open_set)

    # get set of assets which we can convert (smaller than 10USDT)
    redeemable = client.get_small_liability_set()

    # get final list of assets which can be redeemed
    # and are in our earlier set
    final = list(main_set.intersection(redeemable))

    li_of_lis = []
    start = 0
    end = len(final)
    step = 10
    for item in range(start, end, step):
        li_of_lis.append(final[item:item+step])
    # get list of lists containing assets to convert
    # maximum 10 assets per list
    # maximum 3 lists
    # The rest will be discarded, likely picked up on next run
    for current_li in li_of_lis[:3]:
        client.small_liability_exchange(current_li)

if __name__ == '__main__':
    main()
