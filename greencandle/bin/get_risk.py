#!/usr/bin/env python

"""
Send cross margin risk level to nagios periodically
"""

from send_nsca3 import send_nsca
from greencandle.lib.common import arg_decorator
from greencandle.lib.binance_accounts import get_cross_margin_level

@arg_decorator
def main():
    """
    Send cross margin risk level to nagios periodically
    """
    try:
        value = float(get_cross_margin_level())
    except ValueError:
        status = 3
        msg = "UNKNOWN"
        value = "unknown"

    if value >= 2:
        status = 0
        msg = "OK"
    elif value < 2:
        status = 1
        msg = "WARNING"
    elif value < 1.5:
        status = 2
        msg = "CRITICAL"
    else:
        status = 3
        msg = "UNKNOWN"

    send_nsca(status=status, host_name='jenkins1', service_name='cross_margin_risk',
              text_output=f'{msg} risk value is {round(value, 2)};|risk={round(value, 2)}',
              remote_host='10.0.0.212')

    print(value)

if __name__ == '__main__':
    main()
