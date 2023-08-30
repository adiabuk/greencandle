#pylint:disable=too-many-locals
"""
Find and convert small assets without open trades to BNB
"""

from greencandle.lib.auth import binance_auth
from greencandle.lib.mysql import Mysql
from greencandle.lib.common import arg_decorator

@arg_decorator
def main():
    """
    Find and convert small assets without open trades to BNB
    """

    dbase = Mysql()
    client = binance_auth()
    dust_set = client.get_dustable_set()
    open_set = dbase.get_main_open_assets

    # get dust assets which are not in a trade
    main_set = set(dust_set - open_set)

    client.small_dust_exchange(list(main_set))

if __name__ == '__main__':
    main()
