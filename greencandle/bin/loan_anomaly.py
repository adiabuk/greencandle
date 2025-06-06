#!/usr/bin/env python
#pylint: disable=no-member
"""
Get anomalies with debts and send nsca alert to nagios
"""
import sys
from send_nsca3 import send_nsca
from greencandle.lib.auth import binance_auth
from greencandle.lib.common import format_usd, arg_decorator
from greencandle.lib.binance_accounts import base2quote
from greencandle.lib.balance_common import get_base, get_quote
from greencandle.lib.mysql import Mysql
from greencandle.lib import config
from greencandle.lib.logger import get_logger

@arg_decorator
def main():
    """
    Get difference between actual debts from exchange and debts from open db trades"
    """

    logger = get_logger(__name__)
    config.create_config()
    client=binance_auth()
    details = client.get_cross_margin_details()
    debts = {}

    for item in details['userAssets']:
        debt = float(item['borrowed'])
        if debt > 0:
            debts[item['asset']] = debt

    actual_debts = 0
    trade_usd = 0
    for key, val in debts.items():
        usd_debt = val if 'USD' in key else base2quote(val, key+'USDT')
        actual_debts += float(usd_debt)
    dbase = Mysql()
    trade_debts = dbase.fetch_sql_data('select pair, borrowed, direction from trades where '
                                       'close_price is NULL and borrowed > 0', header=False)
    extra_debts_usd = dbase.fetch_sql_data('select sum(borrowed_usd) from extra_loans where '
                                           'date_removed is null', header=False)[0][0]
    for pair, borrowed, direction in trade_debts:
        base = get_base(pair)
        quote = get_quote(pair)
        if direction == 'long':
            if 'USD' in quote:
                trade_usd += float(borrowed)
            else:
                trade_usd += base2quote(borrowed, quote+'USDT')
        elif direction == 'short':
            trade_usd +=  base2quote(borrowed, base+'USDT')

    diff = actual_debts - (trade_usd + (extra_debts_usd if extra_debts_usd else 0))
    if diff > 2000:
        msg = "CRITICAL"
        status = 2
    elif diff > 200:
        msg = "WARNING"
        status = 1
    elif diff < 200:
        msg = 'OK'
        status = 0
    else:
        msg = "UNKNOWN"
        status = 3

    text_output = (f'{msg}: actual: {format_usd(actual_debts)}, '
                   f'in trade:{format_usd(trade_usd)}, diff:{format_usd(diff)}')
    send_nsca(status=status, host_name='eaglenest',
              service_name=f'{config.main.base_env}_loan_anomaly',
              text_output=f'{text_output}|diff={diff};;;;', remote_host='nagios.amrox.loc')
    logger.info(text_output)
    sys.exit(status)

if __name__ == '__main__':
    main()
