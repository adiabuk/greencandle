#pylint:disable=too-many-locals
"""
Find and convert small assets without open trades to BNB
"""

from greencandle.lib.auth import binance_auth
from greencandle.lib.mysql import Mysql
from greencandle.lib.common import arg_decorator
from greencandle.lib.logger import get_logger

@arg_decorator
def main():
    """
    Find and convert small assets without open trades to BNB
    """

    logger = get_logger(__name__)
    dbase = Mysql()
    client = binance_auth()
    dust_set = client.get_dustable_set()
    open_set = dbase.get_main_open_assets()

    # get dust assets which are not in a trade
    main_list = list(set(dust_set - open_set))
    if len(main_list) > 10:
        logger.info("Some assets will be discarded in current run due to max size reached")
    if len(main_list) > 0:
        logger.info("Converting the following small assets to bnb: %s", str(main_list[:10]))
        client.small_dust_exchange(main_list[:10])

if __name__ == '__main__':
    main()
