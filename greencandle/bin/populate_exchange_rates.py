"""
Populate gbp and usd exchange rates in DB for each trade
"""

import time
from greencandle.lib.binance_common import get_all_klines
from greencandle.lib.balance_common import get_quote
from greencandle.lib.common import arg_decorator
from greencandle.lib.mysql import Mysql

def get_price(pair, str_time):
    """
    Get price of given pair for given timeframe
    """
    pattern = '%Y-%m-%d %H:%M:%S'
    epoch = int(time.mktime(time.strptime(str(str_time), pattern)))
    interval = '5m'
    klines = get_all_klines(pair, interval, start_time='{}000'.format(epoch), no_of_klines=1)

    return klines[0]['close']

@arg_decorator
def main():
    """
    Populate gbp and usd exchange rates in DB for each trade
    """
    dbase = Mysql()
    results = dbase.fetch_sql_data("select id, pair, open_time, close_time from trades "
                                   "where new_open_gbp_rate is Null and close_price is not "
                                   "null", header=False)

    #Need to add close_rate and short:
    for trade_id, pair, open_time, close_time in results:
        quote = get_quote(pair)
        if quote == 'USDT':
            open_usd_rate = 1
            close_usd_rate = 1
        else:
            open_usd_rate = get_price(quote+'USDT', open_time)
            close_usd_rate = get_price(quote+'USDT', close_time)
        open_gbp_rate = float(open_usd_rate)/float(get_price('GBPUSDT', open_time))
        close_gbp_rate = float(close_usd_rate)/float(get_price('GBPUSDT', close_time))

        update = ('update trades set new_open_usd_rate="{}", new_open_gbp_rate="{}", '
                  'new_close_usd_rate="{}", new_close_gbp_rate="{}"  '
                  'where id="{}"'.format(open_usd_rate, open_gbp_rate, close_usd_rate,
                                         close_gbp_rate, trade_id))
        dbase.run_sql_statement(update)
        print("\n\n\n")

if __name__ == '__main__':
    main()
