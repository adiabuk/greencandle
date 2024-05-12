#!/usr/bin/env python
"""
Get anomalies with debts and send nsca alert to nagios
"""
import sys
from greencandle.lib.auth import binance_auth
from greencandle.lib.common import format_usd, arg_decorator
from greencandle.lib.binance_accounts import base2quote
from greencandle.lib.mysql import Mysql
from send_nsca3 import send_nsca

@arg_decorator
def main():
    """
    Get difference between actual debts from exchange and debts from open db trades"
    """
    client=binance_auth()
    details = client.get_cross_margin_details()
    debts = {}
    for item in details['userAssets']:
        debt = float(item['borrowed'])
        if debt > 0:
            debts[item['asset']] = debt

    actual_debts = 0
    for key, val in debts.items():
        usd_debt = val if 'USD' in key else base2quote(val, key+'USDT')
        actual_debts += float(usd_debt)
    dbase = Mysql()
    trade_debts = dbase.fetch_sql_data('select sum(borrowed_usd) from trades where close_price '
                                       'is NULL', header=False)[0][0]
    trade_debts = trade_debts if trade_debts else 0
    diff = actual_debts - trade_debts
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
                   f'in trade:{format_usd(trade_debts)}, diff:{format_usd(diff)}')
    send_nsca(status=status, host_name='jenkins1', service_name='debt_anomaly',
              text_output=f'{text_output}|diff={diff}', remote_host='nagios.amrox.loc')
    print(text_output)
    sys.exit(status)

if __name__ == '__main__':
    main()
