#!/usr/bin/env python
#pylint: disable=no-member
"""
Get list of symbols that have a balance yet don't have an associated trade
"""
from send_nsca3 import send_nsca
from greencandle.lib.common import arg_decorator
from greencandle.lib.balance import Balance
from greencandle.lib.balance_common import get_base
from greencandle.lib.mysql import Mysql
from greencandle.lib import config

@arg_decorator
def main():
    """
    Get list of symbols that have a balance that don't have an associated open trade
    """
    dbase = Mysql()
    bal = Balance(test=False)
    config.create_config()

    balances = bal.get_balance()['margin']

    actual = {key for key in balances if key not in ('TOTALS', 'BNB', 'USDT', 'BTC', 'ETH')
              and balances[key]['USD'] > 10}
    expected = {get_base(x[2]) for x in dbase.get_open_trades() }

    anomalous = actual - expected
    print(anomalous, len(anomalous))
    try:
        int(len(anomalous))  # to catch any errors
        if len(anomalous) == 0:
            status = 0
            msg = 'OK'
        elif 0 < len(anomalous) < 2:
            status = 1
            msg = 'WARNING'
        elif len(anomalous) >= 2:
            status = 2
            msg = 'CRITICAL'
        else:
            status = 3
            msg = 'UNKNOWN'
    except (ValueError, TypeError):
        status = 3
        msg = 'UNKNOWN'

    send_nsca(status=status, host_name='jenkins',
              service_name=f'{config.main.base_env}_anomalous_symbols',
              text_output=f'{msg} {len(anomalous)} anomalous symbols found in '
                          f'balance:{anomalous}|num={len(anomalous)}',
              remote_host='nagios.amrox.loc')

if __name__ == '__main__':
    main()
