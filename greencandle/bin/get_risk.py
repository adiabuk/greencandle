#!/usr/bin/env python
#pylint: disable=no-member

"""
Send cross margin risk level to nagios periodically
"""

from send_nsca3 import send_nsca
from greencandle.lib.common import arg_decorator
from greencandle.lib.binance_accounts import get_cross_margin_level
from greencandle.lib.logger import get_logger
from greencandle.lib import config

@arg_decorator
def main():
    """
    Send cross margin risk level to nagios periodically
    """
    logger = get_logger(__name__)
    config.create_config()
    env = config.main.base_env
    try:
        value = float(get_cross_margin_level())
    except ValueError:
        status = 3
        msg = "UNKNOWN"
        value = "unknown"

    if value >= 1.25:
        status = 0
        msg = "OK"
    elif value <= 1.16:
        status = 2
        msg = "CRITICAL"
    elif value > 1.16:
        status = 1
        msg = "WARNING"
    else:
        status = 3
        msg = "UNKNOWN"

    send_nsca(status=status, host_name='eaglenest', service_name=f'{env}-cross_margin_risk',
              text_output=f'{msg} risk value is {round(value, 2)};|risk={round(value, 2)}',
              remote_host='nagios.amrox.loc')
    logger.info("Current risk value is %s", value)

if __name__ == '__main__':
    main()
